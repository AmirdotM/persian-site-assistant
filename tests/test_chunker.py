from site_assistant.ingestion.chunker import chunk_text


def test_empty_input_returns_no_chunks() -> None:
    assert chunk_text("  \n ", source_id="faq", title="FAQ") == []


def test_chunks_keep_source_metadata() -> None:
    chunks = chunk_text(
        "الف\nب\nج",
        source_id="faq",
        title="پرسش‌های متداول",
        max_chars=3,
        overlap_chars=1,
    )
    assert chunks
    assert all(chunk.source_id == "faq" for chunk in chunks)
    assert all(chunk.title == "پرسش‌های متداول" for chunk in chunks)


def test_rejects_invalid_overlap() -> None:
    try:
        chunk_text("متن", source_id="x", title="x", max_chars=10, overlap_chars=10)
    except ValueError:
        return
    raise AssertionError("Expected invalid overlap to raise ValueError")


def test_chunks_never_exceed_max_chars() -> None:
    text = "پ" * 90 + "\n" + "ت" * 90
    chunks = chunk_text(
        text, source_id="long", title="متن بلند", max_chars=50, overlap_chars=10
    )
    assert chunks
    assert all(len(chunk.text) <= 50 for chunk in chunks)
