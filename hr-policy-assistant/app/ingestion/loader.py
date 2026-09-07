from pathlib import Path


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def load_document(file_path: str) -> str:
    

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type: {path.suffix}. "
            f"Supported types: {SUPPORTED_EXTENSIONS}"
        )

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Unable to read the file as UTF-8 text."
        ) from exc