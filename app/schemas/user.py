from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr | None = None
    password_hash: str
    role: str = "USER"
    status: str = "ACTIVE"


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr | None
    role: str
    status: str
    must_change_password: bool
    failed_login_count: int
    locked_until: datetime | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    model_config = ConfigDict(from_attributes=True)