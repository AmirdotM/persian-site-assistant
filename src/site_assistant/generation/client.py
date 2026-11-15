"""Hosted LLM provider client."""

from openai import AsyncOpenAI

from site_assistant.config import settings


class LLMClient:
    def __init__(self) -> None:
        if not settings.llm_api_key or not settings.llm_model:
            raise RuntimeError("Set LLM_API_KEY and LLM_MODEL in .env before generating answers")
        kwargs: dict[str, object] = {
            "api_key": settings.llm_api_key,
            "timeout": settings.llm_timeout_seconds,
        }
        if settings.llm_base_url:
            kwargs["base_url"] = settings.llm_base_url
        self.client = AsyncOpenAI(**kwargs)

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate an answer."""
        response = await self.client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        return content.strip() if content else ""

    async def close(self) -> None:
        """Close the HTTP client and release its connections."""
        await self.client.close()
