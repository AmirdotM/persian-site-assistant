"""Load and clean local source documents."""

import re
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from site_assistant.ingestion.normalization import normalize_persian_text


@dataclass(frozen=True, slots=True)
class SourceDocument:
    source_id: str
    title: str
    text: str
    url: str | None = None


def _markdown_title(text: str, fallback: str) -> str:
    """Use the first Markdown heading as the source title when available."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            if title:
                return title
    return fallback


def _markdown_to_plain_text(text: str) -> str:
    """Remove presentation syntax while preserving readable document content."""
    fence = chr(96) * 3
    tick = chr(96)
    # Keep fenced code content but remove the fence markers.
    text = re.sub(
        re.escape(fence) + r"[\w-]*\s*\n?(.*?)" + re.escape(fence),
        r"\1",
        text,
        flags=re.DOTALL,
    )
    # Keep link and image labels, not their Markdown wrappers or destinations.
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Convert Markdown table rows to compact, readable lines.
    table_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if cells and all(re.fullmatch(r"[-: ]+", cell or "-") for cell in cells):
                continue
            table_lines.append("• " + "؛ ".join(cells))
        else:
            table_lines.append(line)
    text = "\n".join(table_lines)
    # Convert headings and list prefixes into plain text.
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^\s*(?:[-*+] |\d+[.)] )", "• ", text)
    text = re.sub(r"(?m)^\s*>\s?", "", text)
    # Remove common inline emphasis/code markers.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_([^_\n]+)_(?!_)", r"\1", text)
    text = re.sub(
        re.escape(tick) + r"([^" + re.escape(tick) + r"]+)" + re.escape(tick),
        r"\1",
        text,
    )
    text = re.sub(r"(?m)^\s*[-_]{3,}\s*$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_local_documents(directory: Path) -> list[SourceDocument]:
    """Load Markdown, text, and HTML files recursively."""
    documents: list[SourceDocument] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".html"}:
            continue

        raw_text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()

        if suffix == ".html":
            soup = BeautifulSoup(raw_text, "html.parser")
            title = soup.title.get_text(" ", strip=True) if soup.title else path.stem
            for node in soup(["script", "style", "noscript"]):
                node.decompose()
            raw_text = soup.get_text("\n", strip=True)
        elif suffix == ".md":
            title = _markdown_title(raw_text, path.stem)
            raw_text = _markdown_to_plain_text(raw_text)
        else:
            title = path.stem

        clean_text = normalize_persian_text(raw_text)
        if clean_text:
            source_id = path.relative_to(directory).with_suffix("").as_posix()
            documents.append(SourceDocument(source_id, title, clean_text))

    return documents
