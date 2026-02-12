import pytest

from editor.highlighters.core.base_tokenizer import BaseTokenizer
from editor.highlighters.core.registry import HighlightRegistry
from editor.highlighters.core.types import TokenizeResult
from editor.highlighters.tokenizers.plain_tokenizer import PlainTokenizer
from editor.highlighters.tokenizers.json_tokenizer import JsonTokenizer


class DummyTokenizer(BaseTokenizer):
    def get_lang_id(self) -> str:
        return "dummy"

    def tokenize_line(self, line: str, state_stack):
        return TokenizeResult(tokens=[], final_stack=state_stack)


@pytest.fixture
def isolated_registry():
    original = HighlightRegistry._instance
    HighlightRegistry._instance = HighlightRegistry()
    yield HighlightRegistry._instance
    HighlightRegistry._instance = original


def test_registry_singleton_instance(isolated_registry):
    instance = HighlightRegistry.instance()
    assert instance is isolated_registry


def test_registry_registers_tokenizer_and_extension(isolated_registry):
    tokenizer = DummyTokenizer()
    isolated_registry.register("dummy", tokenizer, [".dummy"])

    assert isolated_registry.get_tokenizer("dummy") is tokenizer
    assert isolated_registry.get_lang_for_extension(".dummy") == "dummy"


def test_registry_default_tokenizer_cached(isolated_registry):
    first = isolated_registry.get_default_tokenizer()
    second = isolated_registry.get_default_tokenizer()

    assert isinstance(first, PlainTokenizer)
    assert first is second


def test_registry_extension_map_defaults(isolated_registry):
    assert isolated_registry.get_lang_for_extension(".py") == "python"
    assert isolated_registry.get_lang_for_extension(".js") == "javascript"


def test_registry_register_overrides_extension(isolated_registry):
    tokenizer = JsonTokenizer()
    isolated_registry.register("json", tokenizer, [".py"])

    assert isolated_registry.get_lang_for_extension(".py") == "json"
