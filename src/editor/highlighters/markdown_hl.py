from editor.highlighters.base import BaseHighlighter


class MarkdownHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r"^#{1,6}\s.*$", "cyan", bold=True)
        self.add_pattern(r"\*\*[^*]+\*\*", "white", bold=True)
        self.add_pattern(r"__[^_]+__", "white", bold=True)
        self.add_pattern(r"\*[^*]+\*", "white", italic=True)
        self.add_pattern(r"_[^_]+_", "white", italic=True)
        self.add_pattern(r"`[^`]+`", "orange")
        self.add_pattern(r"^\s*[-*+]\s", "yellow", bold=True)
        self.add_pattern(r"^\s*\d+\.\s", "yellow", bold=True)
        self.add_pattern(r"\[([^\]]+)\]\([^)]+\)", "cyan")
        self.add_pattern(r"^>.*$", "gray", italic=True)
