from editor.highlighters.base import BaseHighlighter


class JavaHighlighter(BaseHighlighter):
    KEYWORDS = [
        "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
        "class", "const", "continue", "default", "do", "double", "else", "enum",
        "extends", "final", "finally", "float", "for", "goto", "if", "implements",
        "import", "instanceof", "int", "interface", "long", "native", "new",
        "package", "private", "protected", "public", "return", "short", "static",
        "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
        "transient", "try", "void", "volatile", "while", "true", "false", "null",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r"/\*.*?\*/", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"@\w+", "yellow")
        self.add_pattern(r"\b\d+\.?\d*[fFdDlL]*\b", "magenta")
