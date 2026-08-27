from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    owner_id: UUID
    title: str
    original_filename: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    storage_path: str
    file_checksum: str

    raw_text: str | None = None
    parsed_json: dict | None = None
    okf_markdown: str | None = None
    okf_metadata: dict | None = None

    status: str = "UPLOADED"
    parse_status: str = "PENDING"
    index_status: str = "PENDING"
    okf_status: str = "PENDING"

    error_message: str | None = None
    version: int = 1
    is_active: bool = True

    llm_config_id: UUID | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None


class DocumentResponse(BaseModel):
    id: UUID
    owner_id: UUID
    title: str
    original_filename: str
    mime_type: str
    file_extension: str
    file_size_bytes: int
    storage_path: str
    file_checksum: str

    raw_text: str | None
    parsed_json: dict | None
    okf_markdown: str | None
    okf_metadata: dict | None

    status: str
    parse_status: str
    index_status: str
    okf_status: str

    error_message: str | None
    version: int
    is_active: bool

    llm_config_id: UUID | None
    created_by: UUID | None
    updated_by: UUID | None

    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)