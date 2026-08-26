from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse


router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)


@router.post("/", response_model=MessageResponse)
def create_message(
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    message = Message(
        **data.model_dump()
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.get("/", response_model=list[MessageResponse])
def list_messages(
    db: Session = Depends(get_db),
):
    return (
        db.query(Message)
        .filter(Message.deleted_at.is_(None))
        .order_by(
            Message.conversation_id,
            Message.sequence_number,
        )
        .all()
    )


@router.get("/{message_id}", response_model=MessageResponse)
def get_message(
    message_id: UUID,
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.deleted_at.is_(None),
        )
        .first()
    )

    if not message:
        raise HTTPException(404, "Message not found")

    return message


@router.put("/{message_id}", response_model=MessageResponse)
def update_message(
    message_id: UUID,
    data: MessageCreate,
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.deleted_at.is_(None),
        )
        .first()
    )

    if not message:
        raise HTTPException(404, "Message not found")

    for key, value in data.model_dump().items():
        setattr(message, key, value)

    message.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(message)

    return message


@router.delete("/{message_id}")
def delete_message(
    message_id: UUID,
    db: Session = Depends(get_db),
):
    message = (
        db.query(Message)
        .filter(
            Message.id == message_id,
            Message.deleted_at.is_(None),
        )
        .first()
    )

    if not message:
        raise HTTPException(404, "Message not found")

    now = datetime.now(timezone.utc)

    message.deleted_at = now
    message.updated_at = now

    db.commit()

    return {
        "message": "Message deleted successfully",
        "message_id": message_id,
    }