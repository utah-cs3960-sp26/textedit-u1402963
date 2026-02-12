import pytest
from editor.highlighters.core.types import StateStack, StackFrame, StyleId, Token
from editor.highlighters.tokenizers.c_tokenizer import CTokenizer
from editor.highlighters.tokenizers.java_tokenizer import JavaTokenizer
from editor.highlighters.tokenizers.javascript_tokenizer import JavaScriptTokenizer


def extract(line, tokens):
    """Return list of (text, style_id) for each token."""
    return [(line[t.start:t.start + t.length], t.style_id) for t in tokens]


EMPTY: StateStack = ()


# ── C Tokenizer ──────────────────────────────────────────────────────────────


class TestCTokenizerKeywords:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_keyword_int(self, tok):
        line = "int x;"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("int", StyleId.KEYWORD) in ex
        assert ("x", StyleId.IDENTIFIER) in ex
        assert (";", StyleId.PUNCTUATION) in ex

    @pytest.mark.parametrize("kw", [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "int", "long", "register", "return", "short", "signed", "sizeof",
        "static", "struct", "switch", "typedef", "union", "unsigned", "void",
        "volatile", "while",
    ])
    def test_all_keywords(self, tok, kw):
        line = f"{kw} x"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == (kw, StyleId.KEYWORD)


class TestCTokenizerComments:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_line_comment(self, tok):
        line = "// this is a comment"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0] == (line, StyleId.COMMENT)

    def test_block_comment_single_line(self, tok):
        line = "x /* comment */ y"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("/* comment */", StyleId.COMMENT) in ex
        assert r.final_stack == EMPTY

    def test_block_comment_open(self, tok):
        line = "/* start"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("/* start", StyleId.COMMENT)
        assert len(r.final_stack) == 1
        assert r.final_stack[-1].lang_id == "c"
        assert r.final_stack[-1].sub_state == 1

    def test_block_comment_continue(self, tok):
        stack: StateStack = (StackFrame("c", 1, None),)
        line = "still in comment"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]
        assert r.final_stack == stack

    def test_block_comment_close(self, tok):
        stack: StateStack = (StackFrame("c", 1, None),)
        line = "end of comment */ code"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.COMMENT
        assert "end of comment */" in ex[0][0]
        assert r.final_stack == EMPTY


class TestCTokenizerStrings:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_double_quote_string(self, tok):
        line = '"hello"'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [('"hello"', StyleId.STRING)]

    def test_escape_in_string(self, tok):
        line = r'"he\"llo"'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING

    def test_char_literal(self, tok):
        line = "'a'"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("'a'", StyleId.STRING)]

    def test_char_escape(self, tok):
        line = r"'\n'"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING


class TestCTokenizerPreprocessor:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_include(self, tok):
        line = "#include"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("#include", StyleId.KEYWORD)

    def test_define(self, tok):
        line = "#define MAX 100"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("#define", StyleId.KEYWORD)

    def test_include_with_space(self, tok):
        line = "# include"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.KEYWORD


class TestCTokenizerNumbers:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_integer(self, tok):
        line = "42"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42", StyleId.NUMBER)]

    def test_hex(self, tok):
        line = "0xFF"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0xFF", StyleId.NUMBER)]

    def test_octal(self, tok):
        line = "012"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("012", StyleId.NUMBER)]

    def test_float(self, tok):
        line = "3.14"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("3.14", StyleId.NUMBER)]

    def test_scientific(self, tok):
        line = "1e10"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("1e10", StyleId.NUMBER)]

    def test_scientific_negative_exp(self, tok):
        line = "1e-5"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("1e-5", StyleId.NUMBER)

    def test_suffix_ul(self, tok):
        line = "42UL"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42UL", StyleId.NUMBER)]

    def test_float_leading_dot(self, tok):
        line = ".5"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [(".5", StyleId.NUMBER)]

    def test_suffix_f(self, tok):
        line = "3.14f"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("3.14f", StyleId.NUMBER)]


class TestCTokenizerOperators:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    @pytest.mark.parametrize("op", ["==", "!=", "++", "--", "->", "<=", ">=", "&&", "||", "<<", ">>"])
    def test_two_char_operators(self, tok, op):
        line = f"a {op} b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (op, StyleId.OPERATOR) in ex

    @pytest.mark.parametrize("op", ["<<=", ">>="])
    def test_three_char_operators(self, tok, op):
        line = f"a {op} b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (op, StyleId.OPERATOR) in ex


class TestCTokenizerPunctuation:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    @pytest.mark.parametrize("ch", ["{", "}", "(", ")", "[", "]", ",", ";"])
    def test_punctuation(self, tok, ch):
        r = tok.tokenize_line(ch, EMPTY)
        ex = extract(ch, r.tokens)
        assert ex == [(ch, StyleId.PUNCTUATION)]


class TestCTokenizerMixed:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_return_statement(self, tok):
        line = "return 0;"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [
            ("return", StyleId.KEYWORD),
            ("0", StyleId.NUMBER),
            (";", StyleId.PUNCTUATION),
        ]

    def test_empty_line(self, tok):
        r = tok.tokenize_line("", EMPTY)
        assert r.tokens == []

    def test_whitespace_only(self, tok):
        r = tok.tokenize_line("   \t  ", EMPTY)
        assert r.tokens == []

    def test_main_function(self, tok):
        line = "int main() {"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("int", StyleId.KEYWORD)
        assert ex[1] == ("main", StyleId.IDENTIFIER)
        assert ex[2] == ("(", StyleId.PUNCTUATION)
        assert ex[3] == (")", StyleId.PUNCTUATION)
        assert ex[4] == ("{", StyleId.PUNCTUATION)


# ── Java Tokenizer ───────────────────────────────────────────────────────────


class TestJavaTokenizerKeywords:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    @pytest.mark.parametrize("kw", [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch",
        "char", "class", "const", "continue", "default", "do", "double",
        "else", "enum", "extends", "final", "finally", "float", "for",
        "goto", "if", "implements", "import", "instanceof", "int", "interface",
        "long", "native", "new", "package", "private", "protected", "public",
        "return", "short", "static", "strictfp", "super", "switch",
        "synchronized", "this", "throw", "throws", "transient", "try",
        "void", "volatile", "while", "true", "false", "null",
    ])
    def test_all_keywords(self, tok, kw):
        line = f"{kw} x"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == (kw, StyleId.KEYWORD)

    def test_boolean_literals(self, tok):
        line = "true false null"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s == StyleId.KEYWORD for _, s in ex)


class TestJavaTokenizerAnnotations:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_annotation(self, tok):
        line = "@Override"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("@Override", StyleId.IDENTIFIER)]

    def test_annotation_with_value(self, tok):
        line = "@SuppressWarnings"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("@SuppressWarnings", StyleId.IDENTIFIER)


class TestJavaTokenizerComments:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_line_comment(self, tok):
        line = "// java comment"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]

    def test_block_comment_single_line(self, tok):
        line = "/* block */"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("/* block */", StyleId.COMMENT)]

    def test_block_comment_open(self, tok):
        line = "/* start"
        r = tok.tokenize_line(line, EMPTY)
        assert r.final_stack[-1].lang_id == "java"
        assert r.final_stack[-1].sub_state == 1

    def test_block_comment_continue(self, tok):
        stack: StateStack = (StackFrame("java", 1, None),)
        line = "middle of block"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]
        assert r.final_stack == stack

    def test_block_comment_close(self, tok):
        stack: StateStack = (StackFrame("java", 1, None),)
        line = "end */ x"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.COMMENT
        assert r.final_stack == EMPTY

    def test_javadoc_style(self, tok):
        line = "/** doc */"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("/** doc */", StyleId.COMMENT)]


class TestJavaTokenizerStrings:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_double_quote(self, tok):
        line = '"hello"'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [('"hello"', StyleId.STRING)]

    def test_char_literal(self, tok):
        line = "'a'"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("'a'", StyleId.STRING)]

    def test_escape_in_string(self, tok):
        line = r'"he\"llo"'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING


class TestJavaTokenizerNumbers:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_integer(self, tok):
        line = "42"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42", StyleId.NUMBER)]

    def test_hex(self, tok):
        line = "0xFF"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0xFF", StyleId.NUMBER)]

    def test_binary(self, tok):
        line = "0b1010"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0b1010", StyleId.NUMBER)]

    def test_long_suffix(self, tok):
        line = "42L"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42L", StyleId.NUMBER)]

    def test_float(self, tok):
        line = "3.14"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("3.14", StyleId.NUMBER)]

    def test_scientific(self, tok):
        line = "1e10"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens)[0] == ("1e10", StyleId.NUMBER)

    def test_underscore_in_number(self, tok):
        line = "1_000_000"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("1_000_000", StyleId.NUMBER)]

    def test_double_suffix(self, tok):
        line = "3.14d"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("3.14d", StyleId.NUMBER)]


class TestJavaTokenizerOperators:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_triple_right_shift(self, tok):
        line = "a >>> b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (">>>", StyleId.OPERATOR) in ex

    def test_triple_right_shift_assign(self, tok):
        line = "a >>>= b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (">>>=", StyleId.OPERATOR) in ex

    def test_method_reference(self, tok):
        line = "a :: b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("::", StyleId.OPERATOR) in ex

    @pytest.mark.parametrize("op", ["==", "!=", "&&", "||", "++", "--", "->"])
    def test_two_char_operators(self, tok, op):
        line = f"a {op} b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (op, StyleId.OPERATOR) in ex


class TestJavaTokenizerMixed:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_string_assignment(self, tok):
        line = 'String s = "hello";'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("String", StyleId.IDENTIFIER)
        assert ex[1] == ("s", StyleId.IDENTIFIER)
        assert ex[2] == ("=", StyleId.OPERATOR)
        assert ex[3] == ('"hello"', StyleId.STRING)
        assert ex[4] == (";", StyleId.PUNCTUATION)

    def test_empty_line(self, tok):
        r = tok.tokenize_line("", EMPTY)
        assert r.tokens == []

    def test_public_class_declaration(self, tok):
        line = "public class Main {"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("public", StyleId.KEYWORD)
        assert ex[1] == ("class", StyleId.KEYWORD)
        assert ex[2] == ("Main", StyleId.IDENTIFIER)
        assert ex[3] == ("{", StyleId.PUNCTUATION)


# ── JavaScript Tokenizer ─────────────────────────────────────────────────────


class TestJSTokenizerKeywords:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    @pytest.mark.parametrize("kw", [
        "break", "case", "catch", "class", "const", "continue", "debugger",
        "default", "delete", "do", "else", "export", "extends", "finally",
        "for", "function", "if", "import", "in", "instanceof", "let", "new",
        "return", "super", "switch", "this", "throw", "try", "typeof", "var",
        "void", "while", "with", "yield", "async", "await", "of",
        "true", "false", "null", "undefined",
    ])
    def test_all_keywords(self, tok, kw):
        line = f"{kw} x"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == (kw, StyleId.KEYWORD)


class TestJSTokenizerStrings:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_double_quote(self, tok):
        line = '"hello"'
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [('"hello"', StyleId.STRING)]

    def test_single_quote(self, tok):
        line = "'hello'"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("'hello'", StyleId.STRING)]

    def test_template_string_single_line(self, tok):
        line = "`hello`"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("`hello`", StyleId.STRING)]

    def test_template_string_multiline_open(self, tok):
        line = "`start"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("`start", StyleId.STRING)]
        assert r.final_stack[-1].lang_id == "javascript"
        assert r.final_stack[-1].sub_state == 2

    def test_template_string_continue(self, tok):
        stack: StateStack = (StackFrame("javascript", 2, None),)
        line = "middle part"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("middle part", StyleId.STRING)]
        assert any(f.sub_state == 2 for f in r.final_stack)

    def test_template_string_close(self, tok):
        stack: StateStack = (StackFrame("javascript", 2, None),)
        line = "end part`"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.STRING
        js_frames = [f for f in r.final_stack if f.sub_state == 2]
        assert len(js_frames) == 0

    def test_template_string_with_escape(self, tok):
        line = r"`he\`llo`"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING

    def test_escape_in_double_quote(self, tok):
        line = r'"he\"llo"'
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING


class TestJSTokenizerComments:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_line_comment(self, tok):
        line = "// js comment"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [(line, StyleId.COMMENT)]

    def test_block_comment_single_line(self, tok):
        line = "/* block */"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("/* block */", StyleId.COMMENT)]

    def test_block_comment_open(self, tok):
        line = "/* open"
        r = tok.tokenize_line(line, EMPTY)
        assert r.final_stack[-1].sub_state == 1

    def test_block_comment_continue(self, tok):
        stack: StateStack = (StackFrame("javascript", 1, None),)
        line = "still commenting"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("still commenting", StyleId.COMMENT)]

    def test_block_comment_close(self, tok):
        stack: StateStack = (StackFrame("javascript", 1, None),)
        line = "end */ code"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.COMMENT


class TestJSTokenizerRegex:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_regex_after_equals(self, tok):
        line = "x = /pattern/g"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("/pattern/g", StyleId.STRING) in ex

    def test_regex_with_char_class(self, tok):
        line = "x = /[a-z]+/"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("/[a-z]+/", StyleId.STRING) in ex

    def test_division_not_regex(self, tok):
        line = "a / b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("a", StyleId.IDENTIFIER) in ex
        assert ("/", StyleId.OPERATOR) in ex
        assert ("b", StyleId.IDENTIFIER) in ex

    def test_regex_at_line_start(self, tok):
        line = "/pattern/"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex == [("/pattern/", StyleId.STRING)]

    def test_regex_with_escape(self, tok):
        line = r"x = /pat\/tern/"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        regex_tokens = [t for t, s in ex if s == StyleId.STRING]
        assert len(regex_tokens) == 1

    def test_regex_with_newline_returns_none(self, tok):
        line = "x = /unterminated\n"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("/", StyleId.OPERATOR) in ex

    def test_regex_rejected_for_comment_prefix(self, tok):
        line = "x = /* comment"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert any(style == StyleId.COMMENT for _, style in ex)

    def test_try_parse_regex_rejects_non_slash(self, tok):
        assert tok._try_parse_regex("abc", 0) is None

    def test_try_parse_regex_rejects_comment_start(self, tok):
        assert tok._try_parse_regex("/*", 0) is None

    def test_try_parse_regex_requires_closing_slash(self, tok):
        assert tok._try_parse_regex("/unterminated", 0) is None


class TestJSTokenizerNumbers:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_integer(self, tok):
        line = "42"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42", StyleId.NUMBER)]

    def test_hex(self, tok):
        line = "0xFF"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0xFF", StyleId.NUMBER)]

    def test_binary(self, tok):
        line = "0b1010"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0b1010", StyleId.NUMBER)]

    def test_octal(self, tok):
        line = "0o777"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("0o777", StyleId.NUMBER)]

    def test_bigint(self, tok):
        line = "42n"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("42n", StyleId.NUMBER)]

    def test_float(self, tok):
        line = "3.14"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("3.14", StyleId.NUMBER)]

    def test_scientific(self, tok):
        line = "1e10"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens)[0] == ("1e10", StyleId.NUMBER)

    def test_underscore(self, tok):
        line = "1_000"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("1_000", StyleId.NUMBER)]


class TestJSTokenizerOperators:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    @pytest.mark.parametrize("op", ["===", "!==", "**=", "??=", "&&=", "||=", ">>>"])
    def test_three_char_operators(self, tok, op):
        line = f"a {op} b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (op, StyleId.OPERATOR) in ex

    def test_four_char_operator_unsigned_shift_assign(self, tok):
        line = "a >>>= b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (">>>=", StyleId.OPERATOR) in ex

    @pytest.mark.parametrize("op", ["=>", "??", "**", "==", "!=", "&&", "||", "++", "--"])
    def test_two_char_operators(self, tok, op):
        line = f"a {op} b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert (op, StyleId.OPERATOR) in ex

    def test_nullish_coalescing(self, tok):
        line = "a ?? b"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("??", StyleId.OPERATOR) in ex


class TestJSTokenizerIdentifiers:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_dollar_identifier(self, tok):
        line = "$element"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("$element", StyleId.IDENTIFIER)]

    def test_underscore_identifier(self, tok):
        line = "_private"
        r = tok.tokenize_line(line, EMPTY)
        assert extract(line, r.tokens) == [("_private", StyleId.IDENTIFIER)]


class TestJSTokenizerMixed:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_arrow_function(self, tok):
        line = "const f = () => 42"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("const", StyleId.KEYWORD)
        assert ex[1] == ("f", StyleId.IDENTIFIER)
        assert ex[2] == ("=", StyleId.OPERATOR)
        assert ("=>", StyleId.OPERATOR) in ex
        assert ("42", StyleId.NUMBER) in ex

    def test_empty_line(self, tok):
        r = tok.tokenize_line("", EMPTY)
        assert r.tokens == []

    def test_punctuation(self, tok):
        line = "({[]})"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert all(s == StyleId.PUNCTUATION for _, s in ex)
        assert len(ex) == 6


class TestCTokenizerEdgeCases:
    @pytest.fixture
    def tok(self):
        return CTokenizer()

    def test_unknown_char_is_skipped(self, tok):
        """Characters like @ that aren't handled should be skipped without crashing."""
        line = "x @ y"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("x", StyleId.IDENTIFIER) in ex
        assert ("y", StyleId.IDENTIFIER) in ex
        # @ is not in any token category for C, should just be skipped


class TestJavaTokenizerEdgeCases:
    @pytest.fixture
    def tok(self):
        return JavaTokenizer()

    def test_get_lang_id(self, tok):
        assert tok.get_lang_id() == "java"

    def test_char_escape_sequence(self, tok):
        line = r"'\n'"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert len(ex) == 1
        assert ex[0][1] == StyleId.STRING

    def test_scientific_with_positive_sign(self, tok):
        line = "1e+5"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("1e+5", StyleId.NUMBER)

    def test_unknown_char_skipped(self, tok):
        line = "x $ y"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        identifiers = [t for t, s in ex if s == StyleId.IDENTIFIER]
        assert "x" in identifiers
        assert "y" in identifiers

    def test_float_leading_dot(self, tok):
        line = ".5"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == (".5", StyleId.NUMBER)


class TestJSTokenizerEdgeCases:
    @pytest.fixture
    def tok(self):
        return JavaScriptTokenizer()

    def test_get_lang_id(self, tok):
        assert tok.get_lang_id() == "javascript"

    def test_scientific_with_positive_sign(self, tok):
        line = "1e+5"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == ("1e+5", StyleId.NUMBER)

    def test_unknown_char_skipped(self, tok):
        line = "x @ y"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ("x", StyleId.IDENTIFIER) in ex
        assert ("y", StyleId.IDENTIFIER) in ex

    def test_template_continue_with_escape(self, tok):
        """Escaped backtick in continuation should not close template string."""
        stack = (StackFrame("javascript", 2, None),)
        line = r"still \` going"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.STRING
        assert any(f.sub_state == 2 for f in r.final_stack)

    def test_regex_not_started_after_slash_star(self, tok):
        """/ followed by * is block comment, not regex."""
        line = "/* comment */"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0][1] == StyleId.COMMENT

    def test_float_leading_dot(self, tok):
        line = ".5"
        r = tok.tokenize_line(line, EMPTY)
        ex = extract(line, r.tokens)
        assert ex[0] == (".5", StyleId.NUMBER)
