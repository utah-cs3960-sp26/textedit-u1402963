from editor.highlighters.base import BaseHighlighter


class JsonHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r'"[^"\\]*(\\.[^"\\]*)*"\s*:', "cyan")
        self.add_pattern(r':\s*"[^"\\]*(\\.[^"\\]*)*"', "orange")
        self.add_pattern(r"\b(true|false|null)\b", "magenta", bold=True)
        self.add_pattern(r"\b-?\d+\.?\d*([eE][+-]?\d+)?\b", "magenta")
