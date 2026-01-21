"""Core highlighting infrastructure."""

from .base_tokenizer import BaseTokenizer
from .incremental_manager import IncrementalManager
from .style_registry import StyleId, StyleRegistry

__all__ = ["BaseTokenizer", "IncrementalManager", "StyleId", "StyleRegistry"]
