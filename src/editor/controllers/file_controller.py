from typing import Tuple, Optional

from editor.file_manager import FileManager
from editor.models.document import DocumentModel
from editor.highlighters.detector import LanguageDetector


class FileController:
    """Controller for file operations, bridging view and model."""

    def __init__(self, document: DocumentModel):
        self.document = document
        self.file_manager = FileManager()

    def open_file(self, file_path: str) -> Tuple[bool, str, str]:
        """
        Open a file and update the document model.

        Returns:
            Tuple of (success, content, error_message)
        """
        try:
            content = self.file_manager.read_file(file_path)
            self.document.file_path = file_path
            self.document.set_content(content, mark_as_saved=True)
            return True, content, ""
        except FileNotFoundError:
            return False, "", f"File not found: {file_path}"
        except PermissionError:
            return False, "", f"Permission denied: {file_path}"
        except UnicodeDecodeError:
            return False, "", f"Could not open file: {file_path}\n\nThis appears to be a binary file. Only text files are supported."
        except Exception as e:
            return False, "", f"Could not open file: {e}"

    def save_file(self, file_path: str, content: str) -> Tuple[bool, str]:
        """
        Save content to a file and update the document model.

        Returns:
            Tuple of (success, error_message)
        """
        final_path = LanguageDetector.suggest_extension(file_path, content)

        try:
            self.file_manager.write_file(final_path, content)
            self.document.file_path = final_path
            self.document.set_content(content, mark_as_saved=True)
            return True, ""
        except PermissionError:
            return False, f"Permission denied: {final_path}"
        except Exception as e:
            return False, f"Could not save file: {e}"

    def get_save_filter(self, content: str) -> str:
        """Get the suggested save filter based on current file and content."""
        return LanguageDetector.get_save_filter(
            self.document.file_path or "", content
        )

    def get_suggested_path(self) -> str:
        """Get the suggested path for save dialog."""
        return self.document.file_path or ""

    @property
    def is_modified(self) -> bool:
        """Check if the document has unsaved changes."""
        return self.document.is_modified

    @property
    def current_file(self) -> Optional[str]:
        """Get the current file path."""
        return self.document.file_path
