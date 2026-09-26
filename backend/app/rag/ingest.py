from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "portfolio"


def load_markdown_documents() -> list[dict]:
    """Load portfolio Markdown documents from the knowledge directory."""

    if not DATA_DIR.exists():
        return []

    documents: list[dict] = []

    for path in sorted(DATA_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()

        if not content:
            continue

        documents.append(
            {
                "source": path.name,
                "content": content,
            }
        )

    return documents


def chunk_document(document: dict) -> list[dict]:
    """Split a Markdown document into deterministic sections."""

    lines = document["content"].splitlines()

    chunks: list[list[str]] = []
    current: list[str] = []

    for line in lines:
        if line.startswith("## ") and current:
            chunks.append(current)
            current = []

        current.append(line)

    if current:
        chunks.append(current)

    results: list[dict] = []

    for index, lines in enumerate(chunks):
        content = "\n".join(lines).strip()

        if not content:
            continue

        results.append(
            {
                "source": document["source"],
                "content": content,
                "chunk": index,
            }
        )

    return results


def load_chunks() -> list[dict]:
    """Load and chunk all portfolio documents."""

    chunks = []

    for document in load_markdown_documents():
        chunks.extend(chunk_document(document))

    return chunks


def ingest() -> list[dict]:
    """Return the current portfolio knowledge chunks."""

    return load_chunks()


if __name__ == "__main__":
    chunks = ingest()

    print(f"Loaded {len(chunks)} chunks.")

    for chunk in chunks:
        print(f"- {chunk['source']} (chunk={chunk['chunk']})")
