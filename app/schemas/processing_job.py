from datetime import datetime
from uuid import UUID
from typing import Literal

from pydantic import BaseModel, Field


class ProcessingJobBase(BaseModel):
    document_id: UUID
    job_type: Literal[
        "PARSE",
        "GENERATE_OKF",
        "CHUNK",
        "EMBED",
        "INDEX",
        "DELETE_INDEX",
    ]
    status: Literal[
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "CANCELLED",
    ] = "QUEUED"
    progress_percentage: int = Field(default=0, ge=0, le=100)
    attempt_count: int = 0
    request_payload: dict | None = None
    result_payload: dict | None = None
    error_code: str | None = None
    error_message: str | None = None
    llm_config_id: UUID | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_by: UUID


class ProcessingJobCreate(ProcessingJobBase):
    pass


class ProcessingJobResponse(ProcessingJobBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
