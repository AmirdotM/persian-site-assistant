"""Tests for recursive source-document loading."""

from site_assistant.ingestion.loader import load_local_documents


def test_loader_uses_markdown_heading_and_nested_source_id(tmp_path) -> None:
    project_dir = tmp_path / "projects"
    project_dir.mkdir()
    document_path = project_dir / "online-store.md"
    document_path.write_text(
        "# سناریوی نمایشی: فروشگاه اینترنتی\n\nتوضیح نمونه فارسی.",
        encoding="utf-8",
    )

    documents = load_local_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].title == "سناریوی نمایشی: فروشگاه اینترنتی"
    assert documents[0].source_id == "projects/online-store"
    assert "توضیح نمونه فارسی" in documents[0].text


def test_loader_removes_html_script_and_style_content(tmp_path) -> None:
    document_path = tmp_path / "page.html"
    document_path.write_text(
        "<html><head><title>صفحه خدمات</title><style>.x{}</style></head>"
        "<body><h1>خدمات</h1><script>alert('x')</script><p>متن صفحه</p></body></html>",
        encoding="utf-8",
    )

    documents = load_local_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].title == "صفحه خدمات"
    assert "متن صفحه" in documents[0].text
    assert "alert" not in documents[0].text
