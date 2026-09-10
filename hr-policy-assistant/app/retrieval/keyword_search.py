import re
from collections import Counter


STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an",
    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "cannot", "could", "did", "do", "does", "doing", "down", "during",
    "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of",
    "off", "on", "once", "only", "or", "other", "ought", "our", "ours",
    "ourselves", "out", "over", "own", "same", "she", "should", "so",
    "some", "such", "than", "that", "the", "their", "theirs", "them",
    "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we",
    "were", "what", "when", "where", "which", "while", "who", "whom",
    "why", "with", "would", "you", "your", "yours", "yourself",
    "yourselves",
    # Question quantifiers, auxiliary query verbs, and document meta terms
    "many", "much", "tell", "give", "take", "get", "provide", "provides",
    "policy", "policies", "s"
}


TOKEN_PATTERN = re.compile(
    r"\b\d+(?:\.\d+)+\b|"
    r"\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b"
)


def stem_token(token: str) -> str:
    """
    Lightweight morphological normalization for English tokens.
    Preserves section numbers like '4.1' and short acronyms.
    """
    if "." in token or token.isdigit():
        return token

    # Adverb/adjective suffixes (annually -> annual, yearly -> year)
    if token.endswith("ally") and len(token) >= 7:
        return token[:-4]
    if token.endswith("ly") and len(token) >= 5:
        return token[:-2]

    # Plural 'ies' -> 'y' (e.g., policies -> policy, entries -> entry)
    if token.endswith("ies") and len(token) >= 5:
        return token[:-3] + "y"

    # Sibilant 'es' plurals (e.g., boxes -> box, watches -> watch)
    if token.endswith(("shes", "ches", "sses", "xes")) and len(token) >= 5:
        return token[:-2]

    # Standard English plurals: strip trailing 's' while preserving root 'e'
    # leaves -> leave, employees -> employee, days -> day, rules -> rule, allowances -> allowance
    if token.endswith("s") and not token.endswith("ss") and len(token) >= 3:
        return token[:-1]

    # Participles and past tense
    if token.endswith("ing") and len(token) >= 6:
        if token.endswith("ying"):
            return token[:-4] + "y"
        return token[:-3]

    if token.endswith("ed") and len(token) >= 5:
        if token.endswith("ied"):
            return token[:-3] + "y"
        return token[:-2]

    return token


def tokenize(
    text: str,
    remove_stopwords: bool = True
) -> list[str]:
    """
    Convert text into normalized tokens.
    """

    if not text:
        return []

    text = text.lower()

    tokens = TOKEN_PATTERN.findall(text)

    if remove_stopwords:
        tokens = [
            token
            for token in tokens
            if token not in STOPWORDS
        ]

    return [stem_token(t) for t in tokens] if tokens else []


def keyword_score(
    query: str,
    document: str
) -> float:
    """
    Calculate lexical overlap between query and document.

    Score:
        0.0 -> no query terms matched
        1.0 -> all query terms matched
    """

    query_tokens = tokenize(query)

    document_tokens = tokenize(document)

    if not query_tokens or not document_tokens:
        return 0.0

    query_counts = Counter(query_tokens)

    document_counts = Counter(document_tokens)

    matched = 0

    for token, query_count in query_counts.items():

        document_count = document_counts.get(
            token,
            0
        )

        matched += min(
            query_count,
            document_count
        )

    return matched / len(query_tokens)