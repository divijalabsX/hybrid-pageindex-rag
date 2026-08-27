from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel


class ConversationBase(BaseModel):
    user_id: UUID
    title: str
    llm_config_id: UUID | None = None
    scope_json: dict = {}
    system_prompt: str | None = None
    status: Literal[
        "ACTIVE",
        "ARCHIVED",
        "DELETED",
    ] = "ACTIVE"


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}