from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel


class MessageBase(BaseModel):
    conversation_id: UUID
    parent_message_id: UUID | None = None
    role: Literal[
        "USER",
        "ASSISTANT",
        "SYSTEM",
    ]
    content: str
    sequence_number: int
    retrieval_query: str | None = None
    citations: dict | None = None
    generation_metadata: dict | None = None
    status: Literal[
        "PENDING",
        "COMPLETED",
        "FAILED",
    ] = "PENDING"
    error_message: str | None = None


class MessageCreate(MessageBase):
    pass


class MessageResponse(MessageBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}