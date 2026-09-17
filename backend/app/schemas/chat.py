import uuid

from pydantic import BaseModel, Field


class ChatMessageRequest(BaseModel):
    session_id: uuid.UUID | None = None
    message: str = Field(min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    session_id: uuid.UUID
    intent: str
    reply: str
    provider_used: str | None = None
    data: dict | None = None
