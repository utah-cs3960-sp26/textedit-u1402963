from editor.highlighters.base import BaseHighlighter


class PlainTextHighlighter(BaseHighlighter):
    def __init__(self, document):
        super().__init__(document)
