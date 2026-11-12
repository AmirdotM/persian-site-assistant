"""Load local source documents."""

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
        else:
            title = path.stem

        clean_text = normalize_persian_text(raw_text)
        if clean_text:
            source_id = path.relative_to(directory).with_suffix("").as_posix()
            documents.append(SourceDocument(source_id, title, clean_text))

    return documents
