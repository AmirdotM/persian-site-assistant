"""Chat API routes."""

from fastapi import APIRouter, HTTPException, Request, status

from site_assistant.api.rate_limit import client_identifier
from site_assistant.config import settings
from site_assistant.schemas import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(payload: ChatRequest, request: Request) -> ChatResponse:
    service = getattr(request.app.state, "chat_service", None)
    if service is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is unavailable.",
        )

    if settings.public_demo_mode:
        limiter = request.app.state.chat_rate_limiter
        allowed, retry_after = limiter.allow(client_identifier(request))
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="تعداد پرسش‌ها در این بازه زیاد است. لطفاً کمی بعد دوباره تلاش کنید.",
                headers={"Retry-After": str(retry_after)},
            )

    response = await service.answer(payload.message, session_id=payload.session_id)
    return response.model_copy(update={"request_id": request.state.request_id})
