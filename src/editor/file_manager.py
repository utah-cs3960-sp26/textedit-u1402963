class FileManager:
    @staticmethod
    def read_file(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def write_file(file_path: str, content: str) -> None:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
