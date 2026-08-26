from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class LLMConfigBase(BaseModel):
    name: str
    provider: str
    purpose: str
    base_url: str | None = None
    model_name: str
    encrypted_api_key: str | None = None
    embedding_dimension: int | None = None
    settings_json: dict = {}
    is_active: bool = True
    is_default: bool = False
    created_by: UUID | None = None


class LLMConfigCreate(LLMConfigBase):
    pass


class LLMConfigResponse(LLMConfigBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}