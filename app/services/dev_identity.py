import os
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User


def get_development_user(db: Session) -> User:
    """
    Temporary development identity.

    Disabled outside APP_ENV=development.
    The user ID is resolved exclusively from backend configuration.
    """

    app_env = os.getenv("APP_ENV", "").strip().lower()

    if app_env != "development":
        raise HTTPException(
            status_code=401,
            detail="Authentication is required",
        )

    configured_user_id = os.getenv("DEV_USER_ID")

    if not configured_user_id:
        raise HTTPException(
            status_code=500,
            detail="Development identity is not configured",
        )

    try:
        user_id = UUID(configured_user_id)
    except ValueError:
        raise HTTPException(
            status_code=500,
            detail="Invalid development identity configuration",
        )

    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.status == "ACTIVE",
            User.deleted_at.is_(None),
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Development user is unavailable",
        )

    return user