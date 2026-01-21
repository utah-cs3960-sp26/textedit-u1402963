import pytest
from editor.highlighters.core.types import StateStack, StackFrame, StyleId
from editor.highlighters.core.stack_pool import StateStackPool
from editor.highlighters.tokenizers.html_tokenizer import HtmlTokenizer
from editor.highlighters.tokenizers.markdown_tokenizer import MarkdownTokenizer
from editor.highlighters.tokenizers.python_tokenizer import PythonTokenizer


class TestStateStackPool:
    @pytest.fixture(autouse=True)
    def reset_pool(self):
        StateStackPool.reset()
        yield
        StateStackPool.reset()

    def test_stack_pool_intern_and_get(self):
        pool = StateStackPool()
        stack: StateStack = (StackFrame(lang_id="html", sub_state=0, end_condition=None),)
        
        state_id = pool.intern(stack)
        retrieved = pool.get(state_id)
        
        assert retrieved == stack

    def test_stack_pool_same_stack_same_id(self):
        pool = StateStackPool()
        stack: StateStack = (StackFrame(lang_id="html", sub_state=0, end_condition=None),)
        
        id1 = pool.intern(stack)
        id2 = pool.intern(stack)
        
        assert id1 == id2

    def test_stack_pool_different_stacks_different_ids(self):
        pool = StateStackPool()
        stack1: StateStack = (StackFrame(lang_id="html", sub_state=0, end_condition=None),)
        stack2: StateStack = (StackFrame(lang_id="javascript", sub_state=0, end_condition=None),)
        
        id1 = pool.intern(stack1)
        id2 = pool.intern(stack2)
        
        assert id1 != id2

    def test_stack_pool_empty_state(self):
        pool = StateStackPool()
        
        result = pool.get(-1)
        
        assert result == ()


class TestHtmlJsTransitions:
    @pytest.fixture
    def tokenizer(self):
        return HtmlTokenizer()

    def test_html_script_tag_pushes_js_state(self, tokenizer):
        initial_stack: StateStack = ()
        
        result = tokenizer.tokenize_line("<script>", initial_stack)
        
        assert len(result.final_stack) >= 1
        js_frame = next((f for f in result.final_stack if f.lang_id == "javascript"), None)
        assert js_frame is not None, "JavaScript frame should be pushed onto stack"

    def test_html_js_content_tokenized(self, tokenizer):
        js_stack: StateStack = (
            StackFrame(lang_id="html", sub_state=0, end_condition=None),
            StackFrame(lang_id="javascript", sub_state=0, end_condition="</script>"),
        )
        
        result = tokenizer.tokenize_line("var x = 1;", js_stack)
        
        assert len(result.tokens) > 0
        embedded_tokens = [t for t in result.tokens if t.style_id == StyleId.EMBEDDED]
        assert len(embedded_tokens) > 0, "JS content should be tokenized as EMBEDDED"

    def test_html_script_close_pops_js_state(self, tokenizer):
        js_stack: StateStack = (
            StackFrame(lang_id="html", sub_state=0, end_condition=None),
            StackFrame(lang_id="javascript", sub_state=0, end_condition="</script>"),
        )
        
        result = tokenizer.tokenize_line("</script>", js_stack)
        
        js_frames = [f for f in result.final_stack if f.lang_id == "javascript"]
        assert len(js_frames) == 0, "JavaScript frame should be popped from stack"

    def test_html_multiline_script(self, tokenizer):
        initial_stack: StateStack = ()
        
        result1 = tokenizer.tokenize_line("<script>", initial_stack)
        assert any(f.lang_id == "javascript" for f in result1.final_stack), \
            "After <script>, JS should be on stack"
        
        result2 = tokenizer.tokenize_line("function foo() {", result1.final_stack)
        assert any(f.lang_id == "javascript" for f in result2.final_stack), \
            "Still in JS mode after function definition"
        
        result3 = tokenizer.tokenize_line("}</script>", result2.final_stack)
        js_frames = [f for f in result3.final_stack if f.lang_id == "javascript"]
        assert len(js_frames) == 0, "After </script>, JS should be popped"


class TestMarkdownCodeBlocks:
    @pytest.fixture
    def tokenizer(self):
        return MarkdownTokenizer()

    def test_markdown_code_fence_pushes_state(self, tokenizer):
        initial_stack: StateStack = ()
        
        result = tokenizer.tokenize_line("```python", initial_stack)
        
        assert len(result.final_stack) > 1, "Code block state should be pushed"
        top_frame = result.final_stack[-1]
        assert top_frame.lang_id == "python", "Language should be python"
        assert top_frame.sub_state == 1, "Should be in STATE_CODE_BLOCK"

    def test_markdown_code_block_content(self, tokenizer):
        code_block_stack: StateStack = (
            StackFrame(lang_id="markdown", sub_state=0, end_condition=None),
            StackFrame(lang_id="python", sub_state=1, end_condition="```"),
        )
        
        result = tokenizer.tokenize_line("def foo():", code_block_stack)
        
        assert len(result.tokens) > 0
        embedded_tokens = [t for t in result.tokens if t.style_id == StyleId.EMBEDDED]
        assert len(embedded_tokens) > 0, "Code block content should be EMBEDDED"

    def test_markdown_code_fence_close_pops_state(self, tokenizer):
        code_block_stack: StateStack = (
            StackFrame(lang_id="markdown", sub_state=0, end_condition=None),
            StackFrame(lang_id="python", sub_state=1, end_condition="```"),
        )
        
        result = tokenizer.tokenize_line("```", code_block_stack)
        
        assert len(result.final_stack) == 1, "Code block state should be popped"
        assert result.final_stack[-1].lang_id == "markdown", "Should be back to markdown"


class TestPythonMultilineStrings:
    @pytest.fixture
    def tokenizer(self):
        return PythonTokenizer()

    def test_python_triple_quote_pushes_state(self, tokenizer):
        initial_stack: StateStack = ()
        
        result = tokenizer.tokenize_line('"""docstring start', initial_stack)
        
        assert len(result.final_stack) >= 1
        top_frame = result.final_stack[-1]
        assert top_frame.lang_id == "python"
        assert top_frame.sub_state == 2, "Should be STATE_TRIPLE_DOUBLE (2)"

    def test_python_triple_quote_continues(self, tokenizer):
        triple_quote_stack: StateStack = (
            StackFrame(lang_id="python", sub_state=2, end_condition=None),
        )
        
        result = tokenizer.tokenize_line("continued string", triple_quote_stack)
        
        assert len(result.tokens) > 0
        string_tokens = [t for t in result.tokens if t.style_id == StyleId.STRING]
        assert len(string_tokens) > 0, "Continued content should be STRING tokens"

    def test_python_triple_quote_ends(self, tokenizer):
        triple_quote_stack: StateStack = (
            StackFrame(lang_id="python", sub_state=2, end_condition=None),
        )
        
        result = tokenizer.tokenize_line('end of docstring"""', triple_quote_stack)
        
        if result.final_stack:
            top_frame = result.final_stack[-1]
            assert top_frame.sub_state == 0 or len(result.final_stack) == 0, \
                "Should be back to default state"

    def test_python_triple_single_quote_pushes_state(self, tokenizer):
        initial_stack: StateStack = ()
        
        result = tokenizer.tokenize_line("'''docstring start", initial_stack)
        
        assert len(result.final_stack) >= 1
        top_frame = result.final_stack[-1]
        assert top_frame.lang_id == "python"
        assert top_frame.sub_state == 1, "Should be STATE_TRIPLE_SINGLE (1)"
