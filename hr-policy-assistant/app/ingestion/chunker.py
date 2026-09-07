import re
from typing import List, Dict


TABLE_LINE_PATTERN = re.compile(r"^\s*\|.*\|\s*$")


def _split_into_blocks(content: str) -> List[str]:
    """
    Split section content into blocks for packing into chunks.

    A Markdown table (a contiguous run of lines starting and
    ending with '|') is kept together as a single atomic block,
    even if it later exceeds max_chars. This prevents a table
    row from being split across two chunks, which would break
    lookups like "does the Standard tier cover dental implants?"
    
    Non-table content is split into paragraph blocks on blank
    lines.
    """

    lines = content.split("\n")
    blocks = []
    buffer: List[str] = []
    in_table = False

    def flush_buffer():
        if buffer:
            blocks.append("\n".join(buffer).strip())
            buffer.clear()

    for line in lines:
        is_table_line = bool(TABLE_LINE_PATTERN.match(line))

        if is_table_line and not in_table:
            flush_buffer()
            in_table = True
            buffer.append(line)

        elif is_table_line and in_table:
            buffer.append(line)

        elif not is_table_line and in_table:
            flush_buffer()
            in_table = False
            if line.strip():
                buffer.append(line)

        else:
            if not line.strip():
                flush_buffer()
            else:
                buffer.append(line)

    flush_buffer()

    return [block for block in blocks if block.strip()]


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

        blocks = _split_into_blocks(content)

        current_text = ""

        for block in blocks:

            is_table_block = block.lstrip().startswith("|")

            candidate = (
                f"{current_text}\n\n{block}".strip()
                if current_text
                else block
            )

            if len(candidate) <= max_chars or not current_text:
                current_text = candidate
            else:
                chunks.append(
                    {
                        "chunk_id": f"{document_name}-{chunk_number}",
                        "document": document_name,
                        "section": section["section"],
                        "text": current_text.strip()
                    }
                )
                chunk_number += 1

                if not is_table_block and overlap > 0:
                    tail = current_text[-overlap:]
                    current_text = f"{tail}\n\n{block}".strip()
                else:
                    current_text = block

        if current_text:
            chunks.append(
                {
                    "chunk_id": f"{document_name}-{chunk_number}",
                    "document": document_name,
                    "section": section["section"],
                    "text": current_text.strip()
                }
            )
            chunk_number += 1
        

    return chunks