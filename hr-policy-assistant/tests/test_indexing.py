from app.ingestion.loader import load_document
from app.ingestion.chunker import chunk_document
from app.ingestion.indexer import PolicyIndexer


file_path = "data/policies/leave-policy.md"

text = load_document(file_path)

chunks = chunk_document(
    text=text,
    document_name="leave-policy.md"
)

print(f"Chunks created: {len(chunks)}")

indexer = PolicyIndexer()

count = indexer.index_chunks(chunks)

print(f"Chunks indexed: {count}")