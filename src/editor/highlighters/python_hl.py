from editor.highlighters.base import BaseHighlighter


class PythonHighlighter(BaseHighlighter):
    KEYWORDS = [
        "False", "None", "True", "and", "as", "assert", "async", "await",
        "break", "class", "continue", "def", "del", "elif", "else", "except",
        "finally", "for", "from", "global", "if", "import", "in", "is",
        "lambda", "nonlocal", "not", "or", "pass", "raise", "return", "try",
        "while", "with", "yield",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"#.*$", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"\b\d+\.?\d*\b", "magenta")
