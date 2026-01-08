from editor.highlighters.base import BaseHighlighter


class CHighlighter(BaseHighlighter):
    KEYWORDS = [
        "auto", "break", "case", "char", "const", "continue", "default", "do",
        "double", "else", "enum", "extern", "float", "for", "goto", "if",
        "inline", "int", "long", "register", "restrict", "return", "short",
        "signed", "sizeof", "static", "struct", "switch", "typedef", "union",
        "unsigned", "void", "volatile", "while", "_Bool", "_Complex", "_Imaginary",
        "bool", "true", "false", "NULL",
    ]

    def __init__(self, document):
        super().__init__(document)
        self.add_keywords(self.KEYWORDS, "cyan")
        self.add_pattern(r"//.*$", "gray", italic=True)
        self.add_pattern(r"/\*.*?\*/", "gray", italic=True)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"'[^'\\]*(\\.[^'\\]*)*'", "orange")
        self.add_pattern(r"#\s*\w+", "magenta")
        self.add_pattern(r"\b\d+\.?\d*[fFlLuU]*\b", "magenta")
