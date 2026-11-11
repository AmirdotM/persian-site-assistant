"""Application service joining retrieval and LLM generation."""

from site_assistant.generation.client import LLMClient
from site_assistant.generation.prompts import SYSTEM_PROMPT_FA, build_user_prompt
from site_assistant.retrieval.retriever import Retriever
from site_assistant.schemas import ChatResponse, SourceReference


class ChatService:
    def __init__(self, retriever: Retriever, llm: LLMClient) -> None:
        self.retriever = retriever
        self.llm = llm

    async def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
        """Generate an answer with source references."""
        hits = self.retriever.search(question)
        if not hits:
            return ChatResponse(
                answer=
                "متأسفم، اطلاعات کافی برای پاسخ به این پرسش در منابع فعلی ندارم." \
                " لطفاً با پشتیبانی شرکت تماس بگیرید."
            )
        answer = await self.llm.generate(
            system_prompt=SYSTEM_PROMPT_FA,
            user_prompt=build_user_prompt(question, hits),
        )
        sources = [
            SourceReference(
                source_id=hit.chunk.source_id,
                title=hit.chunk.title,
                url=hit.chunk.url,
                excerpt=hit.chunk.text[:240],
            )
            for hit in hits
        ]
        return ChatResponse(answer=answer, sources=sources)
