import re
import sys
import pytest

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QTextDocument

from editor.highlighter import (
    PythonHighlighter,
    CHighlighter,
    CppHighlighter,
    JavaHighlighter,
    HtmlHighlighter,
    JsonHighlighter,
    MarkdownHighlighter,
    PlainTextHighlighter,
    LanguageDetector,
)


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance()
    if application is None:
        application = QApplication(sys.argv)
    yield application


class TestPythonHighlighterKeywords:
    def test_python_keywords_include_core_control_flow(self):
        required = {"def", "class", "if", "else", "elif", "for", "while", "return", "import", "from"}
        assert required.issubset(set(PythonHighlighter.KEYWORDS))

    def test_python_keywords_include_boolean_values(self):
        required = {"True", "False", "None"}
        assert required.issubset(set(PythonHighlighter.KEYWORDS))

    def test_python_keywords_include_exception_handling(self):
        required = {"try", "except", "finally", "raise"}
        assert required.issubset(set(PythonHighlighter.KEYWORDS))

    def test_python_keywords_include_async(self):
        required = {"async", "await"}
        assert required.issubset(set(PythonHighlighter.KEYWORDS))


class TestPythonHighlighterBehavior:
    def test_highlighter_has_rules_for_keywords(self, app):
        doc = QTextDocument()
        highlighter = PythonHighlighter(doc)

        assert len(highlighter._highlighting_rules) > 0, "Highlighter should have highlighting rules"

    def test_highlighter_keyword_pattern_matches_def(self, app):
        doc = QTextDocument()
        highlighter = PythonHighlighter(doc)

        keyword_pattern, keyword_fmt = highlighter._highlighting_rules[0]
        text = "def my_function():"
        matches = list(keyword_pattern.finditer(text))

        assert len(matches) > 0, "Keyword pattern should match 'def'"
        assert matches[0].group() == "def"

    def test_highlighter_string_pattern_matches_quoted_text(self, app):
        doc = QTextDocument()
        highlighter = PythonHighlighter(doc)

        has_string_match = False
        for pattern, fmt in highlighter._highlighting_rules:
            matches = list(pattern.finditer('"hello world"'))
            if matches and '"hello world"' in matches[0].group():
                has_string_match = True
                break

        assert has_string_match, "Highlighter should have pattern that matches strings"


class TestHighlighterIntegration:
    def test_language_detector_returns_correct_highlighter_type(self, app):
        doc = QTextDocument()

        python_hl = LanguageDetector.get_highlighter(doc, "test.py")
        assert isinstance(python_hl, PythonHighlighter)

        c_hl = LanguageDetector.get_highlighter(doc, "test.c")
        assert isinstance(c_hl, CHighlighter)

        cpp_hl = LanguageDetector.get_highlighter(doc, "test.cpp")
        assert isinstance(cpp_hl, CppHighlighter)

        java_hl = LanguageDetector.get_highlighter(doc, "Test.java")
        assert isinstance(java_hl, JavaHighlighter)

        html_hl = LanguageDetector.get_highlighter(doc, "index.html")
        assert isinstance(html_hl, HtmlHighlighter)

        json_hl = LanguageDetector.get_highlighter(doc, "config.json")
        assert isinstance(json_hl, JsonHighlighter)

        md_hl = LanguageDetector.get_highlighter(doc, "README.md")
        assert isinstance(md_hl, MarkdownHighlighter)

        txt_hl = LanguageDetector.get_highlighter(doc, "notes.txt")
        assert isinstance(txt_hl, PlainTextHighlighter)


class TestLanguageDetectorExtension:
    def test_python_extensions(self):
        assert LanguageDetector.detect_from_extension("file.py") == "python"
        assert LanguageDetector.detect_from_extension("file.pyw") == "python"
        assert LanguageDetector.detect_from_extension("/path/to/script.py") == "python"

    def test_c_extensions(self):
        assert LanguageDetector.detect_from_extension("file.c") == "c"
        assert LanguageDetector.detect_from_extension("file.h") == "c"

    def test_cpp_extensions(self):
        assert LanguageDetector.detect_from_extension("file.cpp") == "cpp"
        assert LanguageDetector.detect_from_extension("file.hpp") == "cpp"
        assert LanguageDetector.detect_from_extension("file.cc") == "cpp"
        assert LanguageDetector.detect_from_extension("file.cxx") == "cpp"

    def test_java_extension(self):
        assert LanguageDetector.detect_from_extension("Main.java") == "java"

    def test_html_extensions(self):
        assert LanguageDetector.detect_from_extension("index.html") == "html"
        assert LanguageDetector.detect_from_extension("page.htm") == "html"
        assert LanguageDetector.detect_from_extension("config.xml") == "html"

    def test_json_extension(self):
        assert LanguageDetector.detect_from_extension("data.json") == "json"

    def test_markdown_extensions(self):
        assert LanguageDetector.detect_from_extension("README.md") == "markdown"
        assert LanguageDetector.detect_from_extension("doc.markdown") == "markdown"

    def test_plain_text(self):
        assert LanguageDetector.detect_from_extension("file.txt") == "plain"

    def test_unknown_extension(self):
        assert LanguageDetector.detect_from_extension("file.xyz") == ""
        assert LanguageDetector.detect_from_extension("noextension") == ""

    def test_case_insensitive(self):
        assert LanguageDetector.detect_from_extension("FILE.PY") == "python"
        assert LanguageDetector.detect_from_extension("Main.JAVA") == "java"

    def test_empty_path(self):
        assert LanguageDetector.detect_from_extension("") == ""


class TestLanguageDetectorContent:
    def test_detect_python_by_import(self):
        content = "import os\nimport sys\n\ndef main():\n    pass"
        assert LanguageDetector.detect_from_content(content) == "python"

    def test_detect_python_by_class(self):
        content = "from typing import List\n\nclass MyClass:\n    def __init__(self):\n        pass"
        assert LanguageDetector.detect_from_content(content) == "python"

    def test_detect_c_by_include(self):
        content = '#include <stdio.h>\n\nint main() {\n    return 0;\n}'
        assert LanguageDetector.detect_from_content(content) == "c"

    def test_detect_cpp_by_include_and_class(self):
        content = '#include <iostream>\n\nclass MyClass {\npublic:\n    void method();\n};'
        assert LanguageDetector.detect_from_content(content) == "cpp"

    def test_detect_java_by_class(self):
        content = "package com.example;\n\npublic class Main {\n    public static void main(String[] args) {}\n}"
        assert LanguageDetector.detect_from_content(content) == "java"

    def test_detect_html_by_doctype(self):
        content = "<!DOCTYPE html>\n<html>\n<head></head>\n<body></body>\n</html>"
        assert LanguageDetector.detect_from_content(content) == "html"

    def test_detect_html_by_tag(self):
        content = "<html>\n<body>\n<p>Hello</p>\n</body>\n</html>"
        assert LanguageDetector.detect_from_content(content) == "html"

    def test_detect_json_by_structure(self):
        content = '{\n  "name": "test",\n  "value": 123\n}'
        assert LanguageDetector.detect_from_content(content) == "json"

    def test_detect_markdown_by_headers(self):
        content = "# Title\n\n## Section\n\nSome text here."
        assert LanguageDetector.detect_from_content(content) == "markdown"

    def test_plain_text_fallback(self):
        content = "Just some plain text without any recognizable patterns."
        assert LanguageDetector.detect_from_content(content) == "plain"

    def test_empty_content(self):
        assert LanguageDetector.detect_from_content("") == "plain"


class TestLanguageDetectorRealisticFiles:
    def test_realistic_python_file(self):
        content = '''#!/usr/bin/env python3
import os
from pathlib import Path

class FileHandler:
    def __init__(self, path):
        self.path = Path(path)
    
    def read(self):
        return self.path.read_text()

if __name__ == "__main__":
    handler = FileHandler("test.txt")
'''
        assert LanguageDetector.detect_from_content(content) == "python"

    def test_realistic_c_file(self):
        content = '''#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    printf("Hello, World!\\n");
    return 0;
}
'''
        assert LanguageDetector.detect_from_content(content) == "c"

    def test_realistic_cpp_file(self):
        content = '''#include <iostream>
#include <vector>
#include <string>

namespace myapp {

class Application {
public:
    Application() = default;
    void run();
private:
    std::vector<std::string> args_;
};

}
'''
        assert LanguageDetector.detect_from_content(content) == "cpp"

    def test_realistic_java_file(self):
        content = '''package com.example.myapp;

import java.util.List;
import java.util.ArrayList;

public class Main {
    private List<String> items = new ArrayList<>();
    
    public static void main(String[] args) {
        Main app = new Main();
        app.run();
    }
    
    public void run() {
        System.out.println("Hello, World!");
    }
}
'''
        assert LanguageDetector.detect_from_content(content) == "java"

    def test_realistic_html_file(self):
        content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Page</title>
</head>
<body>
    <h1>Welcome</h1>
    <p>This is a paragraph.</p>
</body>
</html>
'''
        assert LanguageDetector.detect_from_content(content) == "html"

    def test_realistic_json_file(self):
        content = '''{
    "name": "my-project",
    "version": "1.0.0",
    "dependencies": {
        "lodash": "^4.17.21"
    },
    "scripts": {
        "start": "node index.js"
    }
}
'''
        assert LanguageDetector.detect_from_content(content) == "json"

    def test_realistic_markdown_file(self):
        content = '''# Project Title

## Description

This is a sample project that demonstrates markdown detection.

## Installation

1. Clone the repository
2. Run `npm install`
3. Start the server

## Usage

- Feature one
- Feature two
- [Documentation](https://example.com)

## License

MIT
'''
        assert LanguageDetector.detect_from_content(content) == "markdown"

    def test_json_array_format(self):
        content = '''[
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
]
'''
        assert LanguageDetector.detect_from_content(content) == "json"


class TestLanguageDetectorIntegration:
    def test_extension_takes_precedence(self):
        python_looking_content = '#include <stdio.h>'
        assert LanguageDetector.detect("file.py", python_looking_content) == "python"

    def test_content_used_when_no_extension(self):
        content = "from typing import List\n\nclass MyClass:\n    def __init__(self):\n        pass"
        assert LanguageDetector.detect("", content) == "python"

    def test_content_used_for_unknown_extension(self):
        content = "public class Main { }"
        assert LanguageDetector.detect("file.unknown", content) == "java"

    def test_empty_extension_and_content(self):
        assert LanguageDetector.detect("", "") == "plain"


class TestSuggestExtension:
    def test_keeps_existing_extension(self):
        assert LanguageDetector.suggest_extension("file.py", "") == "file.py"
        assert LanguageDetector.suggest_extension("file.java", "") == "file.java"

    def test_adds_python_extension(self):
        content = "import os\n\ndef main():\n    pass"
        assert LanguageDetector.suggest_extension("myfile", content) == "myfile.py"

    def test_adds_c_extension(self):
        content = '#include <stdio.h>\nint main() { return 0; }'
        assert LanguageDetector.suggest_extension("program", content) == "program.c"

    def test_adds_java_extension(self):
        content = "public class Main { }"
        assert LanguageDetector.suggest_extension("Main", content) == "Main.java"

    def test_adds_html_extension(self):
        content = "<!DOCTYPE html>\n<html></html>"
        assert LanguageDetector.suggest_extension("index", content) == "index.html"

    def test_adds_json_extension(self):
        content = '{"key": "value"}'
        assert LanguageDetector.suggest_extension("config", content) == "config.json"

    def test_adds_markdown_extension(self):
        content = "# Title\n\n## Section"
        assert LanguageDetector.suggest_extension("README", content) == "README.md"

    def test_adds_txt_for_plain(self):
        content = "Just plain text"
        assert LanguageDetector.suggest_extension("notes", content) == "notes.txt"


class TestOtherHighlighterKeywords:
    def test_c_highlighter_includes_core_keywords(self):
        required = {"int", "void", "return", "if", "else", "for", "while", "struct"}
        assert required.issubset(set(CHighlighter.KEYWORDS))

    def test_cpp_highlighter_includes_cpp_specific_keywords(self):
        required = {"class", "namespace", "template", "public", "private", "virtual"}
        assert required.issubset(set(CppHighlighter.KEYWORDS))

    def test_java_highlighter_includes_core_keywords(self):
        required = {"public", "class", "interface", "extends", "implements", "new"}
        assert required.issubset(set(JavaHighlighter.KEYWORDS))


class TestOtherHighlighterBehavior:
    def test_c_highlighter_has_rules(self, app):
        doc = QTextDocument()
        highlighter = CHighlighter(doc)
        assert len(highlighter._highlighting_rules) > 0, "C highlighter should have rules"

    def test_c_highlighter_pattern_matches_int(self, app):
        doc = QTextDocument()
        highlighter = CHighlighter(doc)
        keyword_pattern, _ = highlighter._highlighting_rules[0]
        matches = list(keyword_pattern.finditer("int main()"))
        assert any(m.group() == "int" for m in matches), "Should match 'int' keyword"

    def test_html_highlighter_has_rules(self, app):
        doc = QTextDocument()
        highlighter = HtmlHighlighter(doc)
        assert len(highlighter._highlighting_rules) > 0, "HTML highlighter should have rules"

    def test_html_highlighter_pattern_matches_tags(self, app):
        doc = QTextDocument()
        highlighter = HtmlHighlighter(doc)
        has_tag_match = False
        for pattern, _ in highlighter._highlighting_rules:
            matches = list(pattern.finditer("<html>"))
            if matches:
                has_tag_match = True
                break
        assert has_tag_match, "HTML highlighter should have pattern matching tags"

    def test_json_highlighter_has_rules(self, app):
        doc = QTextDocument()
        highlighter = JsonHighlighter(doc)
        assert len(highlighter._highlighting_rules) > 0, "JSON highlighter should have rules"

    def test_markdown_highlighter_has_rules(self, app):
        doc = QTextDocument()
        highlighter = MarkdownHighlighter(doc)
        assert len(highlighter._highlighting_rules) > 0, "Markdown highlighter should have rules"

    def test_markdown_highlighter_pattern_matches_header(self, app):
        doc = QTextDocument()
        highlighter = MarkdownHighlighter(doc)
        has_header_match = False
        for pattern, _ in highlighter._highlighting_rules:
            matches = list(pattern.finditer("# Title"))
            if matches:
                has_header_match = True
                break
        assert has_header_match, "Markdown highlighter should have pattern matching headers"


class TestGetSaveFilter:
    def test_returns_python_filter_for_py_file(self):
        assert LanguageDetector.get_save_filter("file.py", "") == "Python (*.py)"

    def test_returns_filter_based_on_content(self):
        content = "public class Main { }"
        assert LanguageDetector.get_save_filter("", content) == "Java (*.java)"

    def test_returns_text_filter_for_unknown_content(self):
        result = LanguageDetector.get_save_filter("file.xyz", "random content")
        assert result == "Text (*.txt)"
