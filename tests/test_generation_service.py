"""Tests for grounded answer formatting and source presentation."""

import asyncio

from site_assistant.generation.prompts import SYSTEM_PROMPT_FA, build_user_prompt
from site_assistant.generation.service import ChatService
from site_assistant.retrieval.vector_store import SearchHit
from site_assistant.ingestion.chunker import TextChunk


class FakeRetriever:
    def __init__(self, hits: list[SearchHit]) -> None:
        self.hits = hits

    def search(self, question: str) -> list[SearchHit]:
        return self.hits


class FakeLLM:
    def __init__(self, answer: str = "پاسخ آزمایشی") -> None:
        self.answer_text = answer
        self.called = False
        self.last_prompt = ""

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.called = True
        self.last_prompt = user_prompt
        assert system_prompt == SYSTEM_PROMPT_FA
        return self.answer_text


def _hit(chunk_id: str, source_id: str, title: str, text: str) -> SearchHit:
    return SearchHit(
        chunk=TextChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            title=title,
            text=text,
        ),
        score=0.8,
    )


def test_context_uses_document_metadata_not_inline_citation_labels() -> None:
    hits = [
        _hit("services:0", "services", "خدمات", "طراحی وب‌سایت و فروشگاه اینترنتی"),
    ]

    prompt = build_user_prompt("چه خدماتی دارید؟", hits)

    assert "عنوان سند: خدمات" in prompt
    assert "شناسه سند: services" in prompt
    assert "[S1]" not in prompt
    assert "[S1]" not in SYSTEM_PROMPT_FA


def test_answer_removes_legacy_markers_and_deduplicates_sources() -> None:
    hits = [
        _hit("services:0", "services", "خدمات", "طراحی وب‌سایت"),
        _hit("services:1", "services", "خدمات", "فروشگاه اینترنتی"),
        _hit("faq:0", "faq", "پرسش‌های متداول", "ساعات کاری"),
    ]
    llm = FakeLLM("طراحی وب‌سایت و فروشگاه اینترنتی خدمات اصلی هستند. [S1] [S2، S3]")

    response = asyncio.run(ChatService(FakeRetriever(hits), llm).answer("چه خدماتی دارید؟"))

    assert "[S1]" not in response.answer
    assert "[S2" not in response.answer
    assert response.answer == "طراحی وب‌سایت و فروشگاه اینترنتی خدمات اصلی هستند."
    assert [source.source_id for source in response.sources] == ["services", "faq"]
    assert llm.called is True
    assert "عنوان سند: خدمات" in llm.last_prompt


def test_no_retrieved_hits_returns_fallback_without_calling_llm() -> None:
    llm = FakeLLM()
    response = asyncio.run(ChatService(FakeRetriever([]), llm).answer("اطلاعات محرمانه؟"))

    assert response.sources == []
    assert "اطلاعات کافی" in response.answer
    assert llm.called is False
