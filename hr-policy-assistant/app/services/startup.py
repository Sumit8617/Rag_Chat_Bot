import logging
from pathlib import Path

from app.ingestion.loader import load_document, SUPPORTED_EXTENSIONS
from app.ingestion.chunker import chunk_document
from app.ingestion.indexer import PolicyIndexer
from app.retrieval.vector_store import VectorStore


logger = logging.getLogger(__name__)

SAMPLE_POLICIES_DIR = Path("data/policies")


def seed_sample_policies_if_empty() -> int:

    vector_store = VectorStore()

    if vector_store.get_all_chunks():
        logger.info(
            "Vector store already has indexed content; "
            "skipping sample-policy seeding."
        )
        return 0

    if not SAMPLE_POLICIES_DIR.exists():
        logger.info(
            "No %s directory found; nothing to seed.",
            SAMPLE_POLICIES_DIR
        )
        return 0

    indexer = PolicyIndexer()
    total_indexed = 0

    for path in sorted(SAMPLE_POLICIES_DIR.iterdir()):

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = load_document(str(path))
        chunks = chunk_document(text=text, document_name=path.name)
        count = indexer.index_chunks(chunks)

        logger.info("Seeded %s -> %d chunks", path.name, count)

        total_indexed += count

    return total_indexed