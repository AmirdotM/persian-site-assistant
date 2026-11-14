"""Application service joining retrieval and LLM generation."""

import re
import textwrap

from site_assistant.generation.client import LLMClient
from site_assistant.generation.prompts import SYSTEM_PROMPT_FA, build_user_prompt
from site_assistant.retrieval.retriever import Retriever
from site_assistant.schemas import ChatResponse, SourceReference

# Remove legacy/model-invented inline labels. The UI presents related documents
# separately, so these labels are redundant and can point to the wrong chunk.
_INLINE_SOURCE_MARKER = re.compile(
    r"\\s*\\[\\s*S\\s*[0-9۰-۹٠-٩]+"
    r"(?:\\s*[,،]\\s*S?\\s*[0-9۰-۹٠-٩]+)*\\s*\\]",
    flags=re.IGNORECASE,
)


def _clean_answer(answer: str) -> str:
    """Remove unsupported inline source markers left over from older prompts."""
    return _INLINE_SOURCE_MARKER.sub("", answer).strip()


def _make_excerpt(text: str, width: int = 220) -> str:
    """Build a readable source preview without cutting a word in half."""
    compact = " ".join(text.split())
    if len(compact) <= width:
        return compact
    excerpt = textwrap.shorten(compact, width=width, placeholder="…")
    return excerpt


class ChatService:
    def __init__(self, retriever: Retriever, llm: LLMClient) -> None:
        self.retriever = retriever
        self.llm = llm

    async def answer(self, question: str, session_id: str | None = None) -> ChatResponse:
        """Generate a grounded answer and return each retrieved document once."""
        hits = self.retriever.search(question)
        if not hits:
            return ChatResponse(
                answer=(
                    "متأسفم، اطلاعات کافی برای پاسخ به این پرسش در منابع فعلی ندارم. "
                    "لطفاً فقط از راه‌های ارتباطی تعریف‌شده در اسناد پیگیری کنید."
                )
            )

        generated_answer = await self.llm.generate(
            system_prompt=SYSTEM_PROMPT_FA,
            user_prompt=build_user_prompt(question, hits),
        )

        # Multiple retrieved chunks can belong to the same document. Keep the
        # highest-ranked chunk as its preview and render one card per document.
        sources_by_id: dict[str, SourceReference] = {}
        for hit in hits:
            source_id = hit.chunk.source_id
            if source_id in sources_by_id:
                continue
            sources_by_id[source_id] = SourceReference(
                source_id=source_id,
                title=hit.chunk.title,
                url=hit.chunk.url,
                excerpt=_make_excerpt(hit.chunk.text),
            )

        return ChatResponse(
            answer=_clean_answer(generated_answer),
            sources=list(sources_by_id.values()),
        )
