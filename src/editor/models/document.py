from typing import Optional


class DocumentModel:
    """Model representing the current document state."""

    def __init__(self):
        self._file_path: Optional[str] = None
        self._dirty: bool = False

    @property
    def file_path(self) -> Optional[str]:
        return self._file_path

    @file_path.setter
    def file_path(self, value: Optional[str]) -> None:
        self._file_path = value

    @property
    def is_modified(self) -> bool:
        return self._dirty

    def mark_dirty(self) -> None:
        """Mark the document as having unsaved changes."""
        self._dirty = True

    def set_content(self, content: str, mark_as_saved: bool = False) -> None:
        """Set document content. If mark_as_saved, clears the dirty flag."""
        if mark_as_saved:
            self._dirty = False

    def mark_saved(self) -> None:
        """Mark document as saved."""
        self._dirty = False

    def reset(self) -> None:
        """Reset the document to initial state."""
        self._file_path = None
        self._dirty = False
