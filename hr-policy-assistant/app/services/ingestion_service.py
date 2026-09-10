from pathlib import Path

from app.ingestion.loader import load_document, SUPPORTED_EXTENSIONS
from app.ingestion.chunker import chunk_document
from app.ingestion.indexer import PolicyIndexer
from app.retrieval.embeddings import EmbeddingService


UPLOAD_DIR = Path("data/policies")


class IngestionService:

    def __init__(self, embedding_service: EmbeddingService | None = None):
        
        self.indexer = PolicyIndexer(embedding_service=embedding_service)
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def ingest_upload(self, filename: str, file_bytes: bytes) -> dict:
        

        if not filename or not filename.strip():
            raise ValueError("Uploaded file has no filename.")

        safe_filename = Path(filename).name
        if not safe_filename or safe_filename.startswith("."):
            raise ValueError("Invalid filename.")

        suffix = Path(safe_filename).suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix}. "
                f"Supported types: {SUPPORTED_EXTENSIONS}"
            )

        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        destination = UPLOAD_DIR / safe_filename
        destination.write_bytes(file_bytes)

        text = load_document(str(destination))

        chunks = chunk_document(
            text=text,
            document_name=safe_filename
        )

        if not chunks:
            raise ValueError(
                "No content could be extracted from the document."
            )

        indexed_count = self.indexer.index_chunks(chunks)

        return {
            "document": safe_filename,
            "chunks_indexed": indexed_count
        }