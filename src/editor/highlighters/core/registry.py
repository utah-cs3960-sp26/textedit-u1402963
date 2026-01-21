from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tokenizers.base_tokenizer import BaseTokenizer


class HighlightRegistry:
    _instance: HighlightRegistry | None = None

    def __init__(self) -> None:
        self._tokenizers: dict[str, BaseTokenizer] = {}
        self._extension_map: dict[str, str] = {}
        self._default_tokenizer: BaseTokenizer | None = None
        self._init_extension_map()

    def _init_extension_map(self) -> None:
        extensions = {
            ".py": "python",
            ".pyw": "python",
            ".c": "c",
            ".h": "c",
            ".cpp": "cpp",
            ".hpp": "cpp",
            ".cc": "cpp",
            ".cxx": "cpp",
            ".hxx": "cpp",
            ".java": "java",
            ".html": "html",
            ".htm": "html",
            ".xml": "html",
            ".json": "json",
            ".md": "markdown",
            ".markdown": "markdown",
            ".js": "javascript",
        }
        self._extension_map.update(extensions)

    @classmethod
    def instance(cls) -> HighlightRegistry:
        if cls._instance is None:
            cls._instance = HighlightRegistry()
        return cls._instance

    def register(
        self,
        lang_id: str,
        tokenizer: BaseTokenizer,
        extensions: list[str],
    ) -> None:
        self._tokenizers[lang_id] = tokenizer
        for ext in extensions:
            self._extension_map[ext] = lang_id

    def get_tokenizer(self, lang_id: str) -> BaseTokenizer | None:
        return self._tokenizers.get(lang_id)

    def get_lang_for_extension(self, ext: str) -> str | None:
        return self._extension_map.get(ext)

    def get_default_tokenizer(self) -> BaseTokenizer:
        if self._default_tokenizer is None:
            from ..tokenizers.plain_tokenizer import PlainTokenizer
            self._default_tokenizer = PlainTokenizer()
        return self._default_tokenizer
