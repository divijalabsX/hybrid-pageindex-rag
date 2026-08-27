from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.document_chunk import DocumentChunk
from app.schemas.document_chunk import (
    DocumentChunkCreate,
    DocumentChunkResponse,
)


router = APIRouter(
    prefix="/document-chunks",
    tags=["Document Chunks"],
)


@router.post("/", response_model=DocumentChunkResponse)
def create_chunk(
    data: DocumentChunkCreate,
    db: Session = Depends(get_db),
):
    chunk = DocumentChunk(
        **data.model_dump()
    )

    db.add(chunk)
    db.commit()
    db.refresh(chunk)

    return chunk


@router.get("/", response_model=list[DocumentChunkResponse])
def list_chunks(
    db: Session = Depends(get_db),
):
    return (
        db.query(DocumentChunk)
        .order_by(
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
        )
        .all()
    )


@router.get("/{chunk_id}", response_model=DocumentChunkResponse)
def get_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
):
    chunk = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.id == chunk_id)
        .first()
    )

    if not chunk:
        raise HTTPException(404, "Document chunk not found")

    return chunk


@router.put("/{chunk_id}", response_model=DocumentChunkResponse)
def update_chunk(
    chunk_id: UUID,
    data: DocumentChunkCreate,
    db: Session = Depends(get_db),
):
    chunk = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.id == chunk_id)
        .first()
    )

    if not chunk:
        raise HTTPException(404, "Document chunk not found")

    for key, value in data.model_dump().items():
        setattr(chunk, key, value)

    db.commit()
    db.refresh(chunk)

    return chunk


@router.delete("/{chunk_id}")
def delete_chunk(
    chunk_id: UUID,
    db: Session = Depends(get_db),
):
    chunk = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.id == chunk_id)
        .first()
    )

    if not chunk:
        raise HTTPException(404, "Document chunk not found")

    db.delete(chunk)
    db.commit()

    return {"message": "Document chunk deleted successfully"}