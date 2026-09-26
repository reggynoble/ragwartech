from .retriever import retrieve

DEFAULT_LIMIT = 3
DEFAULT_MAX_CHARS = 6000


def build_context(
    query: str,
    limit: int = DEFAULT_LIMIT,
    max_chars: int = DEFAULT_MAX_CHARS,
    results: list[dict] | None = None,
) -> str:
    """
    Build deterministic LLM context from retrieved portfolio chunks.
    """

    if limit <= 0 or max_chars <= 0:
        return ""

    if results is None:
        results = retrieve(
            query,
            limit=limit,
        )

    if not results:
        return ""

    sections: list[str] = []
    total_chars = 0

    for result in results[:limit]:
        source = result["source"]
        chunk = result["chunk"]
        content = result["content"]

        section = f"[Source: {source} | Chunk: {chunk}]\n{content.strip()}"

        separator = "\n\n"

        additional_chars = len(section)

        if sections:
            additional_chars += len(separator)

        if total_chars + additional_chars > max_chars:
            remaining = max_chars - total_chars

            if remaining <= 0:
                break

            if sections:
                remaining -= len(separator)

            if remaining <= 0:
                break

            section = section[:remaining]

        sections.append(section)

        total_chars += len(section)

        if total_chars >= max_chars:
            break

    return "\n\n".join(sections)
