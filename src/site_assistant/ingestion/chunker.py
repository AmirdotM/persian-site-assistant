"""Simple paragraph-aware character chunking for the first small corpus."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TextChunk:
    chunk_id: str
    source_id: str
    title: str
    text: str
    url: str | None = None
    chunk_index: int = 0


def chunk_text(
    text: str,
    *,
    source_id: str,
    title: str,
    url: str | None = None,
    max_chars: int = 900,
    overlap_chars: int = 120,
) -> list[TextChunk]:
    """Split text into overlapping chunks."""
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than zero")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError("overlap_chars must be between zero and max_chars - 1")

    paragraphs = [part.strip() for part in text.splitlines() if part.strip()]
    if not paragraphs:
        return []

    blocks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                blocks.append(current)
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                blocks.append(paragraph[start:end])
                if end == len(paragraph):
                    break
                start = end - overlap_chars
            continue

        candidate = f"{current}\n{paragraph}" if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            blocks.append(current)
            available_overlap = max(0, max_chars - len(paragraph) - 1)
            overlap = min(overlap_chars, available_overlap)
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n{paragraph}".strip() if tail else paragraph

    if current:
        blocks.append(current)

    return [
        TextChunk(
            chunk_id=f"{source_id}:{index}",
            source_id=source_id,
            title=title,
            text=block,
            url=url,
            chunk_index=index,
        )
        for index, block in enumerate(blocks)
        if block.strip()
    ]
