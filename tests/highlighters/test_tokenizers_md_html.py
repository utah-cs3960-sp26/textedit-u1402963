import pytest
from editor.highlighters.core.types import StateStack, StackFrame, StyleId, Token
from editor.highlighters.tokenizers.markdown_tokenizer import MarkdownTokenizer
from editor.highlighters.tokenizers.html_tokenizer import HtmlTokenizer


def extract(line, tokens):
    """Return list of (text, style_id) for each token."""
    return [(line[t.start:t.start + t.length], t.style_id) for t in tokens]


EMPTY: StateStack = ()


# ── Markdown Tokenizer ───────────────────────────────────────────────────────


class TestMarkdownHeaders:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    @pytest.mark.parametrize("level", range(1, 7))
    def test_header_levels(self, tok, level):
        line = "#" * level + " Title"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0] == (line, StyleId.KEYWORD)

    def test_not_a_header_no_space(self, tok):
        line = "#NotAHeader"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        # Should NOT be treated as a header (requires space after #)
        assert len(ex) == 0 or ex[0][1] != StyleId.KEYWORD


class TestMarkdownCodeFences:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    def test_code_fence_open_with_language(self, tok):
        line = "```python"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("```python", StyleId.PUNCTUATION)
        top = r.final_stack[-1]
        assert top.lang_id == "python"
        assert top.sub_state == 1  # STATE_CODE_BLOCK
        assert top.end_condition == "```"

    def test_code_fence_open_no_language(self, tok):
        line = "```"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("```", StyleId.PUNCTUATION)
        top = r.final_stack[-1]
        assert top.lang_id == "code"
        assert top.sub_state == 1

    def test_code_block_content(self, tok):
        stack: StateStack = (
            StackFrame("markdown", 0, None),
            StackFrame("python", 1, "```"),
        )
        line = "def foo():"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("def foo():", StyleId.EMBEDDED)]

    def test_code_fence_close(self, tok):
        stack: StateStack = (
            StackFrame("markdown", 0, None),
            StackFrame("python", 1, "```"),
        )
        line = "```"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0] == ("```", StyleId.PUNCTUATION)
        assert len(r.final_stack) == 1
        assert r.final_stack[-1].lang_id == "markdown"

    def test_multiline_code_block_flow(self, tok):
        # Open
        r1 = tok.tokenize_line("```js", EMPTY)
        assert r1.final_stack[-1].lang_id == "js"

        # Content
        r2 = tok.tokenize_line("let x = 1;", r1.final_stack)
        assert extract("let x = 1;", r2.tokens) == [("let x = 1;", StyleId.EMBEDDED)]

        # More content
        r3 = tok.tokenize_line("console.log(x);", r2.final_stack)
        assert extract("console.log(x);", r3.tokens)[0][1] == StyleId.EMBEDDED

        # Close
        r4 = tok.tokenize_line("```", r3.final_stack)
        assert len(r4.final_stack) == 1

    def test_empty_line_in_code_block(self, tok):
        stack: StateStack = (
            StackFrame("markdown", 0, None),
            StackFrame("python", 1, "```"),
        )
        line = ""
        r = tok.tokenize_line(line, stack)
        assert r.tokens == []
        # Should stay in code block
        assert len(r.final_stack) > 1


class TestMarkdownBlockquotes:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    def test_blockquote(self, tok):
        line = "> some quoted text"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]

    def test_nested_blockquote(self, tok):
        line = "> > nested"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]


class TestMarkdownLists:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    def test_unordered_list_dash(self, tok):
        line = "- item"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.PUNCTUATION
        assert ex[0][0] == "- "

    def test_unordered_list_asterisk(self, tok):
        line = "* item"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.PUNCTUATION

    def test_ordered_list(self, tok):
        line = "1. item"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.PUNCTUATION
        assert ex[0][0] == "1. "

    def test_list_with_bold(self, tok):
        line = "- **bold item**"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.PUNCTUATION
        # Bold in the list item text
        bold_tokens = [t for t, s in ex if s == StyleId.KEYWORD]
        assert len(bold_tokens) >= 1


class TestMarkdownInline:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    def test_inline_code(self, tok):
        line = "use `code` here"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("`code`", StyleId.STRING) in ex

    def test_bold_asterisk(self, tok):
        line = "some **bold** text"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("**bold**", StyleId.KEYWORD) in ex

    def test_bold_underscore(self, tok):
        line = "some __bold__ text"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("__bold__", StyleId.KEYWORD) in ex

    def test_italic_asterisk(self, tok):
        line = "some *italic* text"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("*italic*", StyleId.COMMENT) in ex

    def test_italic_underscore(self, tok):
        line = "some _italic_ text"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("_italic_", StyleId.COMMENT) in ex

    def test_link(self, tok):
        line = "[text](https://example.com)"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("[", StyleId.PUNCTUATION) in ex
        assert ("text", StyleId.ATTR_NAME) in ex
        assert ("]", StyleId.PUNCTUATION) in ex
        assert ("(", StyleId.PUNCTUATION) in ex
        assert ("https://example.com", StyleId.STRING) in ex
        assert (")", StyleId.PUNCTUATION) in ex

    def test_link_empty_text(self, tok):
        line = "[](url)"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        # No ATTR_NAME since text is empty
        assert all(s != StyleId.ATTR_NAME for _, s in ex)
        assert ("url", StyleId.STRING) in ex

    def test_plain_text(self, tok):
        line = "just plain text"
        r = tok.tokenize_line(line, EMPTY)
        assert r.tokens == []

    def test_empty_line(self, tok):
        r = tok.tokenize_line("", EMPTY)
        assert r.tokens == []

    def test_unclosed_bold(self, tok):
        line = "some **unclosed"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        # Should not create a bold token since it's unclosed
        assert all(s != StyleId.KEYWORD for _, s in ex)

    def test_mixed_bold_and_italic(self, tok):
        line = "**bold** and *italic*"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("**bold**", StyleId.KEYWORD) in ex
        assert ("*italic*", StyleId.COMMENT) in ex


# ── HTML Tokenizer ───────────────────────────────────────────────────────────


class TestHtmlTags:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_opening_tag(self, tok):
        line = "<div>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        tag_tokens = [t for t, s in ex if s == StyleId.TAG]
        assert len(tag_tokens) >= 2
        assert "<div" in tag_tokens[0]
        assert ">" in tag_tokens[-1]

    def test_closing_tag(self, tok):
        line = "</div>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        tag_tokens = [t for t, s in ex if s == StyleId.TAG]
        assert len(tag_tokens) >= 1

    def test_self_closing_tag(self, tok):
        line = "<br/>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        tag_tokens = [t for t, s in ex if s == StyleId.TAG]
        assert len(tag_tokens) >= 2
        # Should have '/>' somewhere
        assert any("/>" in t for t, s in ex if s == StyleId.TAG)

    def test_self_closing_tag_with_embed_pending(self, tok):
        """Self-closing tags should clear pending embed state."""
        stack = (StackFrame("html", 1, "pending:javascript"),)
        line = "/>"
        r = tok.tokenize_line(line, stack)
        assert r.final_stack[-1].sub_state == 0
        assert r.final_stack[-1].end_condition is None

    def test_tokenizer_default_frame_recovery(self, tok):
        stack = (StackFrame("html", 0, None),)
        line = "&amp;"
        r = tok.tokenize_line(line, stack)
        assert r.tokens

    def test_tokenizer_handles_none_frame(self, tok):
        from editor.highlighters.core.types import StackFrame as CoreStackFrame

        stack = (CoreStackFrame("html", 0, None),)
        with pytest.MonkeyPatch.context() as patcher:
            patcher.setattr(tok, "_current_frame", lambda _stack: None)
            r = tok.tokenize_line("<div>", stack)

        assert r.tokens


class TestHtmlAttributes:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_tag_with_attribute(self, tok):
        line = '<div class="main">'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex
        assert ('"main"', StyleId.ATTR_VALUE) in ex

    def test_attribute_without_value(self, tok):
        line = "<input disabled>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("disabled", StyleId.ATTR_NAME) in ex

    def test_attribute_single_quotes(self, tok):
        line = "<div class='main'>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex
        assert ("'main'", StyleId.ATTR_VALUE) in ex

    def test_attribute_with_extra_spaces_before_equals(self, tok):
        stack = (StackFrame("html", 1, None),)
        line = 'class   ="x">'
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex
        assert ('"x"', StyleId.ATTR_VALUE) in ex


class TestHtmlComments:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_single_line_comment(self, tok):
        line = "<!-- comment -->"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        comment_tokens = [t for t, s in ex if s == StyleId.COMMENT]
        assert len(comment_tokens) >= 1

    def test_multiline_comment_open(self, tok):
        line = "<!-- start"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.COMMENT for _, s in ex)
        # Should be in comment state
        top = r.final_stack[-1]
        assert top.sub_state == 4  # STATE_IN_COMMENT

    def test_multiline_comment_continue(self, tok):
        # Construct a state stack where we're in a comment
        stack: StateStack = (StackFrame("html", 4, None),)
        line = "still in comment"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("still in comment", StyleId.COMMENT)]

    def test_multiline_comment_close(self, tok):
        stack: StateStack = (StackFrame("html", 4, None),)
        line = "end -->"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.COMMENT for _, s in ex)
        # Should be back to default state
        assert r.final_stack[-1].sub_state == 0

    def test_multiline_comment_no_initial_stack(self, tok):
        line = "<!-- comment"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.COMMENT
        assert r.final_stack[-1].sub_state == 4


class TestHtmlScriptEmbed:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_script_tag_pushes_js(self, tok):
        line = "<script>"
        r = tok.tokenize_line(line, EMPTY)
        js_frames = [f for f in r.final_stack if f.lang_id == "javascript"]
        assert len(js_frames) == 1

    def test_script_content_is_embedded(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("javascript", 0, "</script>"),
        )
        line = "var x = 1;"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("var x = 1;", StyleId.EMBEDDED)]

    def test_script_close_pops_js(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("javascript", 0, "</script>"),
        )
        line = "</script>"
        r = tok.tokenize_line(line, stack)
        js_frames = [f for f in r.final_stack if f.lang_id == "javascript"]
        assert len(js_frames) == 0

    def test_script_content_then_close(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("javascript", 0, "</script>"),
        )
        line = "alert(1);</script>"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        embedded = [t for t, s in ex if s == StyleId.EMBEDDED]
        tag = [t for t, s in ex if s == StyleId.TAG]
        assert len(embedded) >= 1
        assert len(tag) >= 1

    def test_script_close_with_uppercase(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("javascript", 0, "</script>"),
        )
        line = "</SCRIPT>"
        r = tok.tokenize_line(line, stack)
        assert all(f.lang_id != "javascript" for f in r.final_stack)


class TestHtmlStyleEmbed:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_style_tag_pushes_css(self, tok):
        line = "<style>"
        r = tok.tokenize_line(line, EMPTY)
        css_frames = [f for f in r.final_stack if f.lang_id == "css"]
        assert len(css_frames) == 1

    def test_style_content_is_embedded(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("css", 0, "</style>"),
        )
        line = "body { color: red; }"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("body { color: red; }", StyleId.EMBEDDED)]

    def test_style_close_pops_css(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("css", 0, "</style>"),
        )
        line = "</style>"
        r = tok.tokenize_line(line, stack)
        css_frames = [f for f in r.final_stack if f.lang_id == "css"]
        assert len(css_frames) == 0

    def test_style_content_then_close(self, tok):
        stack: StateStack = (
            StackFrame("html", 0, None),
            StackFrame("css", 0, "</style>"),
        )
        line = "body{} </style>"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.EMBEDDED for _, s in ex)
        assert any(s == StyleId.TAG for _, s in ex)


class TestHtmlEntities:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_named_entity(self, tok):
        line = "&amp;"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("&amp;", StyleId.KEYWORD)]

    def test_numeric_entity(self, tok):
        line = "&#39;"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("&#39;", StyleId.KEYWORD)]

    def test_hex_entity(self, tok):
        line = "&#x27;"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("&#x27;", StyleId.KEYWORD)]


class TestHtmlMultilineTag:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_tag_split_across_lines(self, tok):
        line1 = "<div"
        r1 = tok.tokenize_line(line1, EMPTY)
        # Should be in STATE_IN_TAG
        assert r1.final_stack[-1].sub_state == 1

        line2 = '  class="x">'
        r2 = tok.tokenize_line(line2, r1.final_stack)
        ex2 = extract(line2, r2.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex2
        assert ('"x"', StyleId.ATTR_VALUE) in ex2
        tag_tokens = [t for t, s in ex2 if s == StyleId.TAG]
        assert any(">" in t for t in tag_tokens)


class TestHtmlMixed:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_plain_text_outside_tags(self, tok):
        line = "hello"
        r = tok.tokenize_line(line, EMPTY)
        # Plain text outside tags should produce no styled tokens
        assert r.tokens == []

    def test_text_between_tags(self, tok):
        # Each tag part processes; text between doesn't get tokens
        line = "<p>Hello</p>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        tag_tokens = [t for t, s in ex if s == StyleId.TAG]
        assert len(tag_tokens) >= 2  # At minimum <p and > and </p and >

    def test_full_document(self, tok):
        lines = ["<html>", "<body>", "<p>Hi</p>", "</body>", "</html>"]
        stack = EMPTY
        for line in lines:
            r = tok.tokenize_line(line, stack)
            stack = r.final_stack
        # After a well-formed document, no embedded states should remain
        assert all(f.lang_id == "html" for f in stack)

    def test_tag_without_name_stays_in_tag_state(self, tok):
        line = "<"
        r = tok.tokenize_line(line, EMPTY)
        assert r.final_stack[-1].sub_state == 1

    def test_attribute_without_value_with_space_after_equals(self, tok):
        line = "<div class= >"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex

    def test_in_tag_whitespace_only_returns(self, tok):
        stack = (StackFrame("html", 1, None),)
        line = "   "
        r = tok.tokenize_line(line, stack)
        assert r.tokens == []
        assert r.final_stack == stack


class TestMarkdownEdgeCases:
    @pytest.fixture
    def tok(self):
        return MarkdownTokenizer()

    def test_get_lang_id(self, tok):
        assert tok.get_lang_id() == "markdown"

    def test_unclosed_inline_code(self, tok):
        line = "use `unclosed code"
        r = tok.tokenize_line(line, EMPTY)
        # Should not create a STRING token since backtick is unclosed
        ex = extract(line, r.tokens)
        assert all(s != StyleId.STRING for _, s in ex)

    def test_unclosed_bold_asterisk(self, tok):
        line = "some **unclosed bold"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.KEYWORD for _, s in ex)

    def test_unclosed_bold_underscore(self, tok):
        line = "some __unclosed bold"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.KEYWORD for _, s in ex)

    def test_unclosed_italic_asterisk(self, tok):
        line = "some *unclosed italic"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.COMMENT for _, s in ex)

    def test_underscore_italic_boundary_check(self, tok):
        """Underscore italic requires word boundary."""
        line = "no_italic_here"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        # Should NOT parse as italic because underscores are mid-word
        assert all(s != StyleId.COMMENT for _, s in ex)

    def test_link_missing_close_bracket(self, tok):
        line = "[unclosed link"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.ATTR_NAME for _, s in ex)

    def test_link_no_paren_after_bracket(self, tok):
        line = "[text] no paren"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.ATTR_NAME for _, s in ex)

    def test_link_missing_close_paren(self, tok):
        line = "[text](unclosed"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.ATTR_NAME for _, s in ex)

    def test_find_single_asterisk_skips_double(self, tok):
        """When searching for single *, ** should be skipped."""
        line = "*bold** and *italic*"
        r = tok.tokenize_line(line, EMPTY)
        # Should find the italic markers, not get confused by **
        ex = extract(line, r.tokens)
        italic_tokens = [t for t, s in ex if s == StyleId.COMMENT]
        assert len(italic_tokens) >= 1

    def test_find_single_underscore_skips_double(self, tok):
        line = "_italic__bold__"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s != StyleId.COMMENT for _, s in ex)

    def test_pop_state_single_frame_returns_same(self, tok):
        stack = (StackFrame("markdown", 0, None),)
        assert tok._pop_state(stack) == stack

    def test_parse_link_invalid_start_returns_none(self, tok):
        assert tok._parse_link("no link", 1, len("no link")) is None


class TestHtmlEdgeCases:
    @pytest.fixture
    def tok(self):
        return HtmlTokenizer()

    def test_opening_tag_no_name(self, tok):
        """< followed by non-alpha should still produce TAG token."""
        line = "< >"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.TAG for _, s in ex)

    def test_closing_tag_no_name(self, tok):
        """</ followed by non-alpha should still produce TAG token."""
        line = "</>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.TAG for _, s in ex)

    def test_attribute_without_quote_value(self, tok):
        """Attribute with = but no quoted value after."""
        line = "<div class=main>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("class", StyleId.ATTR_NAME) in ex

    def test_unknown_char_in_tag(self, tok):
        """Unknown character inside a tag should advance without crashing."""
        line = "<div !weird>"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert any(s == StyleId.TAG for _, s in ex)

    def test_embedded_content_spans_whole_line(self, tok):
        """When no closing tag found, entire line is EMBEDDED."""
        stack = (
            StackFrame("html", 0, None),
            StackFrame("javascript", 0, "</script>"),
        )
        line = "var x = 1; var y = 2;"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.EMBEDDED)]

    def test_update_sub_state_empty_stack(self, tok):
        """_update_sub_state with empty stack should create default frame."""
        result = tok._update_sub_state((), 1)
        assert len(result) == 1
        assert result[0].sub_state == 1

    def test_set_pending_embed_empty_stack(self, tok):
        result = tok._set_pending_embed((), "javascript")
        assert len(result) == 1
        assert result[0].end_condition == "pending:javascript"

    def test_get_pending_embed_empty_stack(self, tok):
        assert tok._get_pending_embed(()) is None

    def test_get_pending_embed_no_pending(self, tok):
        stack = (StackFrame("html", 0, None),)
        assert tok._get_pending_embed(stack) is None

    def test_clear_pending_embed_empty_stack(self, tok):
        result = tok._clear_pending_embed(())
        assert result == ()

    def test_clear_pending_embed_no_pending(self, tok):
        stack = (StackFrame("html", 0, None),)
        result = tok._clear_pending_embed(stack)
        assert result == stack
