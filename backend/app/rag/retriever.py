import re

from .ingest import load_chunks

STOP_WORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "is",
    "are",
    "what",
    "does",
    "do",
    "how",
    "why",
    "where",
    "when",
    "who",
    "use",
    "about",
    "tell",
    "me",
    "for",
    "of",
    "to",
    "in",
    "on",
    "with",
    "portfolio",
    "ragwar",
    "tech",
    # Generic query-intent words.
    "tools",
    "building",
    "kind",
    "type",
    "prefer",
    "system",
    "development",
    "programming",
    "language",
}

QUERY_EXPANSIONS = {
    # Architecture / terminology.
    "server-side": "backend",
    "server side": "backend",
    "built": "build",
    # Technology vocabulary.
    "programming language": "python",
    "database technology": "database sql sqlite",
    "frontend technologies": "frontend html css javascript",
    "frontend technology": "frontend html css javascript",
    "apis": "api rest http",
    # AI / RAG vocabulary.
    "artificial intelligence": "ai llm",
    "rag": "retrieval augmented generation",
}


MIN_RETRIEVAL_SCORE = 4
MIN_RELEVANCE_RATIO = 0.5


def normalize(text: str) -> str:
    """
    Normalize text and apply deterministic query expansions.

    Expansions bridge common user terminology with the vocabulary
    used in the portfolio knowledge base.
    """
    normalized = text.lower()

    for phrase, replacement in QUERY_EXPANSIONS.items():
        normalized = normalized.replace(
            phrase,
            replacement,
        )

    return normalized


def tokenize(text: str) -> list[str]:
    """
    Convert text into normalized retrieval tokens.

    Tokens shorter than three characters and generic query-intent
    words are excluded.
    """
    normalized = normalize(text)

    words = re.findall(
        r"[a-zA-Z0-9]+",
        normalized,
    )

    return [word for word in words if len(word) > 2 and word not in STOP_WORDS]


def _heading_text(content: str) -> str:
    """
    Extract Markdown heading text from a document chunk.
    """
    return " ".join(
        line.lstrip("#").strip()
        for line in content.splitlines()
        if line.startswith("#")
    )


def _score_chunk(
    query: str,
    content: str,
) -> int:
    """
    Calculate a deterministic relevance score for a chunk.

    Scoring factors:
    - matched query terms
    - query coverage
    - heading matches
    - exact phrase matches
    - multiple matches within the same sentence
    """
    query_words = set(tokenize(query))

    if not query_words:
        return 0

    content_words = set(tokenize(content))

    matched_words = query_words & content_words

    if not matched_words:
        return 0

    score = len(matched_words) * 2

    coverage = len(matched_words) / len(query_words)

    if coverage >= 0.75:
        score += 4
    elif coverage >= 0.5:
        score += 2

    heading = _heading_text(content)
    heading_words = set(tokenize(heading))

    heading_matches = query_words & heading_words

    score += len(heading_matches) * 8

    normalized_query = normalize(query)
    normalized_content = normalize(content)

    if len(query_words) >= 2 and normalized_query in normalized_content:
        score += 8

    sentences = re.split(
        r"[.!?]\s+|\n+",
        normalized_content,
    )

    for sentence in sentences:
        sentence_words = set(tokenize(sentence))
        sentence_matches = query_words & sentence_words

        match_count = len(sentence_matches)

        if match_count >= 4 or match_count >= 3:
            score += 2
        elif match_count >= 2:
            score += 3

    return score


def retrieve(
    query: str,
    limit: int = 3,
) -> list[dict]:
    """
    Retrieve the most relevant portfolio chunks for a query.

    Retrieval is deterministic and requires no external API,
    network access, or embedding model.

    At most one chunk is returned per source document.
    """
    if limit <= 0:
        return []

    chunks = load_chunks()

    scored = []

    for chunk in chunks:
        score = _score_chunk(
            query,
            chunk["content"],
        )

        if score >= MIN_RETRIEVAL_SCORE:
            scored.append(
                {
                    **chunk,
                    "score": score,
                }
            )

    if not scored:
        return []

    scored.sort(
        key=lambda item: (
            -item["score"],
            item["source"],
            item["chunk"],
        )
    )

    best_score = scored[0]["score"]

    minimum_score = max(
        MIN_RETRIEVAL_SCORE,
        best_score * MIN_RELEVANCE_RATIO,
    )

    scored = [item for item in scored if item["score"] >= minimum_score]

    # Prefer distinct sources so the retrieved context represents
    # multiple portfolio documents when several sources are relevant.
    selected = []
    sources = set()

    for item in scored:
        if item["source"] in sources:
            continue

        selected.append(item)
        sources.add(item["source"])

        if len(selected) >= limit:
            break

    return selected
