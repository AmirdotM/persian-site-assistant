"""Pydantic schemas define the public HTTP API contract."""

from pydantic import BaseModel, Field, HttpUrl, field_validator


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)

    @field_validator("message")
    @classmethod
    def strip_and_validate_message(cls, value: str) -> str:
        """Reject messages that are empty or contain only whitespace."""
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank.")
        return value


class SourceReference(BaseModel):
    source_id: str
    title: str
    url: HttpUrl | None = None
    excerpt: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference] = Field(default_factory=list)
    request_id: str | None = None
