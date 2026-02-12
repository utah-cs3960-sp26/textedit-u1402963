"""Comprehensive tests for JSON and Python tokenizers."""

import pytest

from editor.highlighters.core.types import (
    StateStack, StackFrame, StyleId, Token, TokenizeResult,
)
from editor.highlighters.tokenizers.json_tokenizer import JsonTokenizer
from editor.highlighters.tokenizers.python_tokenizer import (
    PythonTokenizer,
    STATE_DEFAULT,
    STATE_TRIPLE_SINGLE,
    STATE_TRIPLE_DOUBLE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract(line: str, tokens: list[Token]) -> list[tuple[str, int]]:
    """Return list of (text, style_id) for each token."""
    return [(line[t.start:t.start + t.length], t.style_id) for t in tokens]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def json_tok() -> JsonTokenizer:
    return JsonTokenizer()


@pytest.fixture
def py_tok() -> PythonTokenizer:
    return PythonTokenizer()


EMPTY_STACK: StateStack = ()


# ===========================================================================
#  JSON TOKENIZER TESTS
# ===========================================================================


class TestJsonStringKeyVsValue:
    """JSON: string classification as ATTR_NAME vs STRING."""

    def test_key_value_pair(self, json_tok):
        """'\"name\": \"value\"' -> key is ATTR_NAME, value is STRING."""
        line = '"name": "value"'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ('"name"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
            ('"value"', StyleId.STRING),
        ]

    def test_string_alone_is_value(self, json_tok):
        """'\"hello\"' with no colon following -> STRING."""
        line = '"hello"'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [('"hello"', StyleId.STRING)]

    def test_key_with_spaces_before_colon(self, json_tok):
        """'\"key\"  :' -> ATTR_NAME even with spaces before colon."""
        line = '"key"  :'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ('"key"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
        ]

    def test_string_value_after_colon(self, json_tok):
        """String that appears after a colon is STRING, not ATTR_NAME."""
        line = '"k": "v"'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert ('"v"', StyleId.STRING) in pairs


class TestJsonPunctuation:
    """JSON: punctuation tokens."""

    @pytest.mark.parametrize("ch", ["{", "}", "[", "]", ":", ","])
    def test_individual_punctuation(self, json_tok, ch):
        result = json_tok.tokenize_line(ch, EMPTY_STACK)
        pairs = extract(ch, result.tokens)
        assert pairs == [(ch, StyleId.PUNCTUATION)]


class TestJsonNumbers:
    """JSON: number literal variants."""

    @pytest.mark.parametrize(
        "line",
        ["42", "-3", "3.14", "1e10", "-0.5", "1E+2", "0.123e-4"],
    )
    def test_number(self, json_tok, line):
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [(line, StyleId.NUMBER)]


class TestJsonKeywords:
    """JSON: true, false, null."""

    @pytest.mark.parametrize("kw", ["true", "false", "null"])
    def test_keyword(self, json_tok, kw):
        result = json_tok.tokenize_line(kw, EMPTY_STACK)
        pairs = extract(kw, result.tokens)
        assert pairs == [(kw, StyleId.KEYWORD)]


class TestJsonEscapedString:
    """JSON: escaped quotes inside strings."""

    def test_escaped_quote(self, json_tok):
        line = r'"he\"llo"'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert len(pairs) == 1
        assert pairs[0][1] == StyleId.STRING
        assert pairs[0][0] == line  # whole thing is one token


class TestJsonFullObject:
    """JSON: full object tokenization."""

    def test_full_object(self, json_tok):
        line = '{"key": 42, "flag": true}'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("{", StyleId.PUNCTUATION),
            ('"key"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
            ("42", StyleId.NUMBER),
            (",", StyleId.PUNCTUATION),
            ('"flag"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
            ("true", StyleId.KEYWORD),
            ("}", StyleId.PUNCTUATION),
        ]


class TestJsonArray:
    """JSON: array tokenization."""

    def test_array(self, json_tok):
        line = "[1, 2, 3]"
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("[", StyleId.PUNCTUATION),
            ("1", StyleId.NUMBER),
            (",", StyleId.PUNCTUATION),
            ("2", StyleId.NUMBER),
            (",", StyleId.PUNCTUATION),
            ("3", StyleId.NUMBER),
            ("]", StyleId.PUNCTUATION),
        ]


class TestJsonNested:
    """JSON: nested object tokenization."""

    def test_nested_objects(self, json_tok):
        line = '{"a": {"b": 1}}'
        result = json_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("{", StyleId.PUNCTUATION),
            ('"a"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
            ("{", StyleId.PUNCTUATION),
            ('"b"', StyleId.ATTR_NAME),
            (":", StyleId.PUNCTUATION),
            ("1", StyleId.NUMBER),
            ("}", StyleId.PUNCTUATION),
            ("}", StyleId.PUNCTUATION),
        ]


class TestJsonEmptyAndWhitespace:
    """JSON: empty and whitespace-only lines."""

    def test_empty_line(self, json_tok):
        result = json_tok.tokenize_line("", EMPTY_STACK)
        assert result.tokens == []

    def test_whitespace_only(self, json_tok):
        result = json_tok.tokenize_line("   \t  ", EMPTY_STACK)
        assert result.tokens == []

    def test_state_passthrough(self, json_tok):
        """State stack should be passed through unchanged."""
        result = json_tok.tokenize_line("42", EMPTY_STACK)
        assert result.final_stack == EMPTY_STACK


# ===========================================================================
#  PYTHON TOKENIZER TESTS
# ===========================================================================


class TestPythonKeywords:
    """Python: keyword recognition."""

    def test_def_foo(self, py_tok):
        line = "def foo():"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("def", StyleId.KEYWORD),
            ("foo", StyleId.IDENTIFIER),
            ("(", StyleId.PUNCTUATION),
            (")", StyleId.PUNCTUATION),
            (":", StyleId.PUNCTUATION),
        ]

    @pytest.mark.parametrize(
        "kw",
        [
            "if", "else", "elif", "for", "while", "class", "return",
            "import", "from", "as", "try", "except", "finally", "with",
            "lambda", "yield", "raise", "pass", "break", "continue",
            "and", "or", "not", "in", "is", "None", "True", "False",
            "async", "await",
        ],
    )
    def test_all_keywords_recognized(self, py_tok, kw):
        result = py_tok.tokenize_line(kw, EMPTY_STACK)
        pairs = extract(kw, result.tokens)
        assert pairs == [(kw, StyleId.KEYWORD)]


class TestPythonComments:
    """Python: comment handling."""

    def test_full_line_comment(self, py_tok):
        line = "# this is a comment"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [(line, StyleId.COMMENT)]

    def test_inline_comment(self, py_tok):
        line = "x = 1  # comment"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        # Before the comment
        assert ("x", StyleId.IDENTIFIER) == pairs[0]
        assert ("=", StyleId.OPERATOR) == pairs[1]
        assert ("1", StyleId.NUMBER) == pairs[2]
        # The comment is the last token and covers the rest of the line
        assert pairs[3] == ("# comment", StyleId.COMMENT)


class TestPythonStrings:
    """Python: string literals."""

    def test_single_quoted(self, py_tok):
        line = "'hello'"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [("'hello'", StyleId.STRING)]

    def test_double_quoted(self, py_tok):
        line = '"world"'
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [('"world"', StyleId.STRING)]

    def test_escape_in_double_string(self, py_tok):
        line = r'"he\nllo"'
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert len(pairs) == 1
        assert pairs[0][1] == StyleId.STRING
        assert pairs[0][0] == line


class TestPythonTripleDoubleQuotedStrings:
    """Python: triple double-quoted string handling."""

    def test_single_line_complete(self, py_tok):
        line = '"""hello"""'
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [('"""hello"""', StyleId.STRING)]
        assert result.final_stack == EMPTY_STACK

    def test_multi_line_open(self, py_tok):
        line = '"""start'
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [('"""start', StyleId.STRING)]
        # State should be pushed with sub_state=STATE_TRIPLE_DOUBLE
        assert len(result.final_stack) == 1
        assert result.final_stack[-1].lang_id == "python"
        assert result.final_stack[-1].sub_state == STATE_TRIPLE_DOUBLE

    def test_continuation_line(self, py_tok):
        """Middle line of a triple-quoted string -> entire line is STRING."""
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_DOUBLE, end_condition=None),
        )
        line = "middle line content"
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        assert pairs == [(line, StyleId.STRING)]
        # State should remain (string is not closed)
        assert result.final_stack == triple_state

    def test_closing_line(self, py_tok):
        """Line that closes the triple-quoted string."""
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_DOUBLE, end_condition=None),
        )
        line = 'end"""'
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        assert pairs == [('end"""', StyleId.STRING)]
        # State should be popped
        assert result.final_stack == EMPTY_STACK

    def test_closing_with_code_after(self, py_tok):
        """Close triple-quote and have code afterwards."""
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_DOUBLE, end_condition=None),
        )
        line = 'end""" + x'
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        assert pairs[0] == ('end"""', StyleId.STRING)
        # Remaining tokens after the string
        assert ("+", StyleId.OPERATOR) in pairs
        assert ("x", StyleId.IDENTIFIER) in pairs


class TestPythonTripleSingleQuotedStrings:
    """Python: triple single-quoted string handling."""

    def test_single_line_complete(self, py_tok):
        line = "'''hello'''"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [("'''hello'''", StyleId.STRING)]
        assert result.final_stack == EMPTY_STACK

    def test_multi_line_open(self, py_tok):
        line = "'''start"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [("'''start", StyleId.STRING)]
        assert len(result.final_stack) == 1
        assert result.final_stack[-1].sub_state == STATE_TRIPLE_SINGLE

    def test_continuation_line(self, py_tok):
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_SINGLE, end_condition=None),
        )
        line = "middle"
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        assert pairs == [("middle", StyleId.STRING)]
        assert result.final_stack == triple_state

    def test_closing_line(self, py_tok):
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_SINGLE, end_condition=None),
        )
        line = "end'''"
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        assert pairs == [("end'''", StyleId.STRING)]
        assert result.final_stack == EMPTY_STACK


class TestPythonDecorators:
    """Python: decorator handling."""

    def test_simple_decorator(self, py_tok):
        line = "@decorator"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [("@decorator", StyleId.IDENTIFIER)]

    def test_dotted_decorator(self, py_tok):
        line = "@module.decorator"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [("@module.decorator", StyleId.IDENTIFIER)]


class TestPythonNumbers:
    """Python: number literal variants."""

    @pytest.mark.parametrize(
        "line,expected_text",
        [
            ("42", "42"),
            ("0xFF", "0xFF"),
            ("0b1010", "0b1010"),
            ("0o777", "0o777"),
            ("3.14", "3.14"),
            ("1e-5", "1e-5"),
            ("3j", "3j"),
            ("1_000_000", "1_000_000"),
        ],
    )
    def test_number_literal(self, py_tok, line, expected_text):
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [(expected_text, StyleId.NUMBER)]


class TestPythonOperators:
    """Python: operator tokenization."""

    @pytest.mark.parametrize(
        "op",
        ["=", "==", "!=", "+=", "//", "**", "->", ":="],
    )
    def test_two_char_or_single_operators(self, py_tok, op):
        result = py_tok.tokenize_line(op, EMPTY_STACK)
        pairs = extract(op, result.tokens)
        assert pairs == [(op, StyleId.OPERATOR)]

    def test_two_char_operator_followed_by_text(self, py_tok):
        line = "== x"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert ("==", StyleId.OPERATOR) in pairs

    @pytest.mark.parametrize(
        "op",
        ["//=", "**=", "<<=", ">>="],
    )
    def test_three_char_operators(self, py_tok, op):
        result = py_tok.tokenize_line(op, EMPTY_STACK)
        pairs = extract(op, result.tokens)
        assert pairs == [(op, StyleId.OPERATOR)]


class TestPythonPunctuation:
    """Python: punctuation tokens."""

    @pytest.mark.parametrize(
        "ch", ["(", ")", "[", "]", "{", "}", ":", ",", ".", ";"]
    )
    def test_individual_punctuation(self, py_tok, ch):
        result = py_tok.tokenize_line(ch, EMPTY_STACK)
        pairs = extract(ch, result.tokens)
        assert pairs == [(ch, StyleId.PUNCTUATION)]


class TestPythonMixed:
    """Python: mixed token lines."""

    def test_for_loop(self, py_tok):
        line = "for i in range(10):"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("for", StyleId.KEYWORD),
            ("i", StyleId.IDENTIFIER),
            ("in", StyleId.KEYWORD),
            ("range", StyleId.IDENTIFIER),
            ("(", StyleId.PUNCTUATION),
            ("10", StyleId.NUMBER),
            (")", StyleId.PUNCTUATION),
            (":", StyleId.PUNCTUATION),
        ]

    def test_lambda_expression(self, py_tok):
        line = "x = lambda a, b: a + b"
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        pairs = extract(line, result.tokens)
        assert pairs == [
            ("x", StyleId.IDENTIFIER),
            ("=", StyleId.OPERATOR),
            ("lambda", StyleId.KEYWORD),
            ("a", StyleId.IDENTIFIER),
            (",", StyleId.PUNCTUATION),
            ("b", StyleId.IDENTIFIER),
            (":", StyleId.PUNCTUATION),
            ("a", StyleId.IDENTIFIER),
            ("+", StyleId.OPERATOR),
            ("b", StyleId.IDENTIFIER),
        ]


class TestPythonEmptyAndWhitespace:
    """Python: empty and whitespace-only lines."""

    def test_empty_line(self, py_tok):
        result = py_tok.tokenize_line("", EMPTY_STACK)
        assert result.tokens == []

    def test_whitespace_only(self, py_tok):
        result = py_tok.tokenize_line("    \t  ", EMPTY_STACK)
        assert result.tokens == []


class TestPythonTripleQuoteEscapes:
    """Python: escape sequences inside triple-quoted strings."""

    def test_escaped_triple_quote_does_not_close(self, py_tok):
        r"""Inside a triple-double-quoted continuation, '\"""' should NOT close."""
        triple_state: StateStack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_DOUBLE, end_condition=None),
        )
        line = '\\"""'
        result = py_tok.tokenize_line(line, triple_state)
        pairs = extract(line, result.tokens)
        # The backslash escapes the first ", so it should NOT be a closing triple-quote.
        # The whole line is consumed as part of the string; the trailing " is unmatched
        # so it stays in triple-quote state.
        assert pairs[0][1] == StyleId.STRING
        # Check: after escaping the first quote, we only have `"` left (2 chars),
        # which is not a triple-quote, so state should remain open.
        assert len(result.final_stack) == 1
        assert result.final_stack[-1].sub_state == STATE_TRIPLE_DOUBLE


class TestPythonStateStackTransitions:
    """Python: verify final_stack after opening/closing triple strings."""

    def test_open_then_close(self, py_tok):
        """Open triple-quote on one line, close on the next."""
        # Line 1: open
        line1 = '"""docstring start'
        r1 = py_tok.tokenize_line(line1, EMPTY_STACK)
        assert len(r1.final_stack) == 1
        assert r1.final_stack[-1].sub_state == STATE_TRIPLE_DOUBLE

        # Line 2: close
        line2 = 'docstring end"""'
        r2 = py_tok.tokenize_line(line2, r1.final_stack)
        assert r2.final_stack == EMPTY_STACK

    def test_no_state_change_for_regular_strings(self, py_tok):
        """Regular single/double-quoted strings do not alter state_stack."""
        line = '"hello" + \'world\''
        result = py_tok.tokenize_line(line, EMPTY_STACK)
        assert result.final_stack == EMPTY_STACK

    def test_triple_single_state_transition(self, py_tok):
        """Open triple-single-quote, verify state, close, verify empty."""
        line1 = "'''open"
        r1 = py_tok.tokenize_line(line1, EMPTY_STACK)
        assert len(r1.final_stack) == 1
        assert r1.final_stack[-1].sub_state == STATE_TRIPLE_SINGLE

        line2 = "close'''"
        r2 = py_tok.tokenize_line(line2, r1.final_stack)
        assert r2.final_stack == EMPTY_STACK

    def test_default_state_stack_empty(self, py_tok):
        """Default state with regular code -> empty final_stack."""
        result = py_tok.tokenize_line("x = 42", EMPTY_STACK)
        assert result.final_stack == EMPTY_STACK


class TestJsonEdgeCases:
    @pytest.fixture
    def tok(self):
        return JsonTokenizer()

    def test_get_lang_id(self, tok):
        assert tok.get_lang_id() == "json"

    def test_unknown_char_skipped(self, tok):
        line = "@ stuff"
        r = tok.tokenize_line(line, EMPTY_STACK)
        # Should not crash, tokens should be empty or only for recognized parts

    def test_scientific_with_positive_exponent(self, tok):
        line = "1e+5"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ex[0] == ("1e+5", StyleId.NUMBER)

    def test_negative_float(self, tok):
        line = "-3.14"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ex[0] == ("-3.14", StyleId.NUMBER)


class TestPythonEdgeCases:
    @pytest.fixture
    def tok(self):
        return PythonTokenizer()

    def test_get_lang_id(self, tok):
        assert tok.get_lang_id() == "python"

    def test_triple_quote_with_escape_at_end(self, tok):
        """Escaped quote inside triple-quoted string should not close it."""
        line = '"""hello\\"'
        r = tok.tokenize_line(line, EMPTY_STACK)
        # The backslash-escaped quote should not end the triple string
        assert len(r.final_stack) >= 1
        assert r.final_stack[-1].sub_state == 2

    def test_triple_quote_continuation_closes_later(self, tok):
        stack = (
            StackFrame(lang_id="python", sub_state=STATE_TRIPLE_SINGLE, end_condition=None),
        )
        line = "done'''"
        r = tok.tokenize_line(line, stack)
        ex = extract(line, r.tokens)
        assert ex == [("done'''", StyleId.STRING)]
        assert r.final_stack == EMPTY_STACK

    def test_three_char_operator_matched_before_two_char(self, tok):
        """//= should match as one 3-char operator, not // then =."""
        line = "a //= b"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ("//=", StyleId.OPERATOR) in ex

    def test_power_assign(self, tok):
        line = "a **= b"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ("**=", StyleId.OPERATOR) in ex

    def test_left_shift_assign(self, tok):
        line = "a <<= b"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ("<<=", StyleId.OPERATOR) in ex

    def test_right_shift_assign(self, tok):
        line = "a >>= b"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert (">>=", StyleId.OPERATOR) in ex

    def test_unknown_char_skipped(self, tok):
        """Characters like $ not in Python syntax should be skipped."""
        line = "x $ y"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ("x", StyleId.IDENTIFIER) in ex
        assert ("y", StyleId.IDENTIFIER) in ex

    def test_complex_number(self, tok):
        line = "3j"
        r = tok.tokenize_line(line, EMPTY_STACK)
        ex = extract(line, r.tokens)
        assert ex[0] == ("3j", StyleId.NUMBER)
