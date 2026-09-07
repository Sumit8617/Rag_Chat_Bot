import re
from collections import Counter


def tokenize(text: str) -> list[str]:
  

    text = text.lower()

    tokens = re.findall(
        r"\b\d+(?:\.\d+)+\b|\b[a-zA-Z0-9]+\b",
        text
    )

    return tokens


def keyword_score(
    query: str,
    document: str
) -> float:

    query_tokens = tokenize(query)
    document_tokens = tokenize(document)

    if not query_tokens or not document_tokens:
        return 0.0

    query_counts = Counter(query_tokens)
    document_counts = Counter(document_tokens)

    matched = 0

    for token, count in query_counts.items():

        if token in document_counts:

            matched += min(
                count,
                document_counts[token]
            )

    return matched / len(query_tokens)