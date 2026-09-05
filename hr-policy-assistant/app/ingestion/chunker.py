import re
from typing import List, Dict


def chunk_document(
    text: str,
    document_name: str,
    max_chars: int = 1200,
    overlap: int = 150
) -> List[Dict]:
    """
    Split a policy document into section-aware chunks.

    Each chunk contains:
    - document name
    - section heading
    - chunk id
    - chunk text
    """

    if not text or not text.strip():
        return []

    lines = text.splitlines()

    sections = []
    current_section = "General"
    current_content = []

    for line in lines:

        # Markdown heading: #, ##, ###, etc.
        heading_match = re.match(r"^\s*#{1,6}\s+(.+?)\s*$", line)

        if heading_match:
            # Save previous section
            if current_content:
                sections.append(
                    {
                        "section": current_section,
                        "content": "\n".join(current_content).strip()
                    }
                )

            current_section = heading_match.group(1).strip()
            current_content = []

        else:
            current_content.append(line)

    # Save final section
    if current_content:
        sections.append(
            {
                "section": current_section,
                "content": "\n".join(current_content).strip()
            }
        )

    chunks = []
    chunk_number = 0

    for section in sections:

        content = section["content"]

        if not content:
            continue

        # If section is small enough, keep it together.
        if len(content) <= max_chars:

            chunks.append(
                {
                    "chunk_id": f"{document_name}-{chunk_number}",
                    "document": document_name,
                    "section": section["section"],
                    "text": content
                }
            )

            chunk_number += 1
            continue

        # Split large sections while keeping overlap.
        start = 0

        while start < len(content):

            end = start + max_chars
            chunk_text = content[start:end]

            chunks.append(
                {
                    "chunk_id": f"{document_name}-{chunk_number}",
                    "document": document_name,
                    "section": section["section"],
                    "text": chunk_text.strip()
                }
            )

            chunk_number += 1

            if end >= len(content):
                break

            start = end - overlap

    return chunks