from typing import Optional


class DocumentModel:
    """Model representing the current document state."""

    def __init__(self):
        self._file_path: Optional[str] = None
        self._original_content: str = ""
        self._current_content: str = ""

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @file_path.setter
    def file_path(self, value: Optional[str]) -> None:
        self._file_path = value

    @property
    def original_content(self) -> str:
        return self._original_content

    @property
    def current_content(self) -> str:
        return self._current_content

    @current_content.setter
    def current_content(self, value: str) -> None:
        self._current_content = value

    @property
    def is_modified(self) -> bool:
        return self._current_content != self._original_content

    def set_content(self, content: str, mark_as_saved: bool = False) -> None:
        """Set document content. If mark_as_saved, also updates original content."""
        self._current_content = content
        if mark_as_saved:
            self._original_content = content

    def mark_saved(self) -> None:
        """Mark current content as saved (original = current)."""
        self._original_content = self._current_content

    def reset(self) -> None:
        """Reset the document to initial state."""
        self._file_path = None
        self._original_content = ""
        self._current_content = ""
