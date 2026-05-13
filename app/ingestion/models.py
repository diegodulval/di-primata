from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class IncomingMessage(BaseModel):
    phone: str
    profile_name: str
    body: str
    message_sid: str
    num_media: int = 0
    media_urls: list[str] = Field(default_factory=list)
    received_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class QueueItem(BaseModel):
    id: UUID
    phone: str
    messages: list[IncomingMessage]
    status: str
    process_after: datetime
    created_at: datetime
    processed_at: datetime | None = None
