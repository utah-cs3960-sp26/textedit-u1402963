# Re-export from core to avoid duplicate base class definitions
from editor.highlighters.core.base_tokenizer import BaseTokenizer

__all__ = ["BaseTokenizer"]
