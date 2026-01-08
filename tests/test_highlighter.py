import re
import pytest

from editor.highlighter import PythonHighlighter


class TestPythonHighlighterKeywords:
    def test_all_python_keywords_present(self):
        expected_keywords = {
            "False", "None", "True", "and", "as", "assert", "async", "await",
            "break", "class", "continue", "def", "del", "elif", "else", "except",
            "finally", "for", "from", "global", "if", "import", "in", "is",
            "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
            "while", "with", "yield",
        }
        assert set(PythonHighlighter.KEYWORDS) == expected_keywords

    def test_keyword_count(self):
        assert len(PythonHighlighter.KEYWORDS) == 35


class TestPythonHighlighterRegex:
    @pytest.fixture
    def keyword_pattern(self):
        pattern = r"\b(" + "|".join(PythonHighlighter.KEYWORDS) + r")\b"
        return re.compile(pattern)

    def test_matches_def_keyword(self, keyword_pattern):
        text = "def my_function():"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 1
        assert matches[0].group() == "def"
        assert matches[0].start() == 0
        assert matches[0].end() == 3

    def test_matches_class_keyword(self, keyword_pattern):
        text = "class MyClass:"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 1
        assert matches[0].group() == "class"

    def test_matches_import_keyword(self, keyword_pattern):
        text = "import os"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 1
        assert matches[0].group() == "import"

    def test_matches_multiple_keywords(self, keyword_pattern):
        text = "from os import path"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group() == "from"
        assert matches[1].group() == "import"

    def test_does_not_match_keyword_in_identifier(self, keyword_pattern):
        text = "define = 1"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 0

    def test_does_not_match_keyword_as_substring(self, keyword_pattern):
        text = "class_name = 'MyClass'"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 0

    def test_matches_keyword_at_end_of_line(self, keyword_pattern):
        text = "x = None"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 1
        assert matches[0].group() == "None"

    def test_matches_keyword_with_punctuation(self, keyword_pattern):
        text = "if(True):"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group() == "if"
        assert matches[1].group() == "True"

    def test_matches_async_await(self, keyword_pattern):
        text = "async def fetch(): await response"
        matches = list(keyword_pattern.finditer(text))
        keywords = [m.group() for m in matches]
        assert "async" in keywords
        assert "def" in keywords
        assert "await" in keywords

    def test_empty_string(self, keyword_pattern):
        matches = list(keyword_pattern.finditer(""))
        assert len(matches) == 0

    def test_no_keywords(self, keyword_pattern):
        text = "x = 42 + y"
        matches = list(keyword_pattern.finditer(text))
        assert len(matches) == 0
