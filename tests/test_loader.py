"""Tests for recursive source-document loading."""

from pathlib import Path

from site_assistant.ingestion.chunker import chunk_text
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



def test_expanded_demo_knowledge_base_contains_all_content_areas() -> None:
    documents = load_local_documents(Path("data/raw/demo_company"))
    source_ids = {document.source_id for document in documents}

    expected_source_ids = {
        "website-delivery",
        "ecommerce-solutions",
        "internal-tools",
        "security-and-privacy",
        "support-and-handover",
        "project-scoping-and-estimation",
        "projects/knowledge-assistant",
        "products/catalog",
        "products/selection-guide",
        "products/webnama",
        "products/bazarino",
        "products/paygir",
        "products/jaryankar",
        "products/anbarban",
        "products/didban",
        "products/daneshyar",
        "products/nobatyar",
    }

    assert expected_source_ids.issubset(source_ids)
    assert len(documents) >= 24
    assert all(document.text.strip() for document in documents)



def test_loader_strips_markdown_syntax_from_source_text(tmp_path) -> None:
    document_path = tmp_path / "guide.md"
    document_path.write_text(
        "# راهنمای محصول\n\n"
        "این **محصول** برای تیم‌ها مناسب است.\n\n"
        "- مورد اول\n"
        "- مورد دوم\n\n"
        "برای [جزئیات بیشتر](https://example.test) مراجعه کنید.\n",
        encoding="utf-8",
    )

    document = load_local_documents(tmp_path)[0]

    assert document.title == "راهنمای محصول"
    assert "محصول" in document.text
    assert "• مورد اول" in document.text
    assert "جزئیات بیشتر" in document.text
    assert "**" not in document.text
    assert "https://example.test" not in document.text
    assert not document.text.startswith("#")



def test_loader_converts_markdown_table_rows_to_plain_text(tmp_path) -> None:
    document_path = tmp_path / "catalog.md"
    document_path.write_text(
        "# کاتالوگ\n\n"
        "| شناسه | محصول | قیمت |\n"
        "|---|---|---|\n"
        "| RNA-01 | وب‌نما | ۲۰ تا ۳۰ میلیون تومان |\n",
        encoding="utf-8",
    )

    document = load_local_documents(tmp_path)[0]

    assert "RNA-01" in document.text
    assert "وب‌نما" in document.text
    assert "۲۰ تا ۳۰ میلیون تومان" in document.text
    assert "|" not in document.text



def test_product_selection_guide_fits_one_retrieval_chunk() -> None:
    documents = load_local_documents(Path("data/raw/demo_company/products"))
    guide = next(document for document in documents if document.source_id == "selection-guide")

    chunks = chunk_text(
        guide.text,
        source_id=guide.source_id,
        title=guide.title,
        max_chars=900,
        overlap_chars=120,
    )

    assert len(chunks) == 1
    for product_id in (
        "RNA-WEB-01",
        "RNA-SHOP-02",
        "RNA-CRM-03",
        "RNA-FLOW-04",
        "RNA-STOCK-05",
        "RNA-INSIGHT-06",
        "RNA-KNOW-07",
        "RNA-BOOK-08",
    ):
        assert product_id in chunks[0].text
