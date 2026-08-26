from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class DocumentChunkBase(BaseModel):
    document_id: UUID
    document_version: int
    chunk_index: int
    content: str
    content_hash: str
    token_count: int | None = None
    page_number: int | None = None
    section_path: str | None = None
    chunk_metadata: dict = {}
    embedding: list[float] | None = Field(
        default=None,
        min_length=1536,
        max_length=1536
    )
    embedding_model: str | None = None


class DocumentChunkCreate(DocumentChunkBase):
    pass


class DocumentChunkResponse(DocumentChunkBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}