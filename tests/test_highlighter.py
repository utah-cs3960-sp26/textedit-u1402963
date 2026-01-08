import re
import pytest

from editor.highlighter import (
    PythonHighlighter,
    CHighlighter,
    CppHighlighter,
    JavaHighlighter,
    HtmlHighlighter,
    JsonHighlighter,
    MarkdownHighlighter,
    LanguageDetector,
)


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

    def test_cpp_with_template(self):
        content = '''#include <vector>

template<typename T>
class Container {
    std::vector<T> items;
};
'''
        assert LanguageDetector.detect_from_content(content) == "cpp"

    def test_java_interface(self):
        content = '''public interface Runnable {
    void run();
}
'''
        assert LanguageDetector.detect_from_content(content) == "java"


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


class TestHighlighterClasses:
    def test_c_highlighter_has_keywords(self):
        assert "int" in CHighlighter.KEYWORDS
        assert "void" in CHighlighter.KEYWORDS
        assert "return" in CHighlighter.KEYWORDS

    def test_cpp_highlighter_has_keywords(self):
        assert "class" in CppHighlighter.KEYWORDS
        assert "namespace" in CppHighlighter.KEYWORDS
        assert "template" in CppHighlighter.KEYWORDS

    def test_java_highlighter_has_keywords(self):
        assert "public" in JavaHighlighter.KEYWORDS
        assert "class" in JavaHighlighter.KEYWORDS
        assert "interface" in JavaHighlighter.KEYWORDS
