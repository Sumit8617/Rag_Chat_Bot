from pathlib import Path

from app.ingestion.loader import load_document, SUPPORTED_EXTENSIONS
from app.ingestion.chunker import chunk_document
from app.ingestion.indexer import PolicyIndexer


UPLOAD_DIR = Path("data/policies")


class IngestionService:

    def __init__(self):
        self.indexer = PolicyIndexer()
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def ingest_upload(self, filename: str, file_bytes: bytes) -> dict:
        """
        Save an uploaded policy file to disk, chunk it, and
        index it. Re-uploading a file with the same name
        replaces its previously indexed chunks.
        """

        if not filename:
            raise ValueError("Uploaded file has no filename.")

        suffix = Path(filename).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: {SUPPORTED_EXTENSIONS}"
            )

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        destination = UPLOAD_DIR / filename
        destination.write_bytes(file_bytes)

        text = load_document(str(destination))

        chunks = chunk_document(
            text=text,
            document_name=filename
        )

        if not chunks:
            raise ValueError(
                "No content could be extracted from the document."
            )

        indexed_count = self.indexer.index_chunks(chunks)

        return {
            "document": filename,
            "chunks_indexed": indexed_count
        }