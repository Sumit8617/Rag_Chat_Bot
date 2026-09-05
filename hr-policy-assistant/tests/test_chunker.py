from app.ingestion.loader import load_document
from app.ingestion.chunker import chunk_document


file_path = "data/policies/benefits-policy.md"

text = load_document(file_path)

chunks = chunk_document(
    text=text,
    document_name="benefits-policy.md"
)

print(f"\nTotal chunks: {len(chunks)}\n")

for chunk in chunks:
    print("=" * 60)
    print(f"Chunk ID : {chunk['chunk_id']}")
    print(f"Document: {chunk['document']}")
    print(f"Section : {chunk['section']}")
    print(f"Text    : {chunk['text']}")