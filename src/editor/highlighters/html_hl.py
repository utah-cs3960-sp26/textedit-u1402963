from editor.highlighters.base import BaseHighlighter


class HtmlHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.add_pattern(r"</?[\w-]+", "cyan", bold=True)
        self.add_pattern(r"/?>", "cyan", bold=True)
        self.add_pattern(r"\b[\w-]+(?==)", "yellow")
        self.add_pattern(r'"[^"]*"', "orange")
        self.add_pattern(r"'[^']*'", "orange")
        self.add_pattern(r"<!--.*?-->", "gray", italic=True)
        self.add_pattern(r"&\w+;", "magenta")
