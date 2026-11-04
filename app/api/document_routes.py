import os
from datetime import datetime, timezone
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentCreate,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentUpdate,
)
from app.services.document_storage import save_uploaded_file
from app.services.dev_identity import get_development_user


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# --------------------------------------------------
# 1. Upload document to the database-backed library
# --------------------------------------------------

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=201,
)
async def upload_document_to_library(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    stored = await save_uploaded_file(file)

    document = Document(
        id=stored["id"],
        owner_id=user.id,
        title=os.path.splitext(
            stored["original_filename"]
        )[0][:500],
        original_filename=stored["original_filename"],
        mime_type=file.content_type or "application/octet-stream",
        file_extension=stored["extension"],
        file_size_bytes=stored["file_size_bytes"],
        storage_path=stored["storage_path"],
        file_checksum=stored["file_checksum"],
        status="UPLOADED",
        parse_status="PENDING",
        index_status="PENDING",
        okf_status="PENDING",
        version=1,
        is_active=True,
        created_by=user.id,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()

        # Best-effort cleanup if database persistence fails.
        try:
            os.remove(stored["storage_path"])
        except OSError:
            pass

        raise HTTPException(
            status_code=500,
            detail="Could not save document metadata",
        )

    return document


# --------------------------------------------------
# 2. List documents belonging to the current user
# --------------------------------------------------

@router.get(
    "/",
    response_model=list[DocumentUploadResponse],
)
def list_documents(
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    return (
        db.query(Document)
        .filter(
            Document.owner_id == user.id,
            Document.deleted_at.is_(None),
        )
        .order_by(Document.created_at.desc())
        .all()
    )


# --------------------------------------------------
# 3. Get document processing status
# --------------------------------------------------

@router.get(
    "/{document_id}/status",
    response_model=DocumentUploadResponse,
)
def get_document_status(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == user.id,
            Document.deleted_at.is_(None),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


# --------------------------------------------------
# 4. Get one document
# --------------------------------------------------

@router.get(
    "/{document_id}",
    response_model=DocumentUploadResponse,
)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == user.id,
            Document.deleted_at.is_(None),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


# --------------------------------------------------
# 5. Update permitted document metadata
# --------------------------------------------------

@router.patch(
    "/{document_id}",
    response_model=DocumentUploadResponse,
)
def update_document(
    document_id: UUID,
    document_data: DocumentUpdate,
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == user.id,
            Document.deleted_at.is_(None),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    title = document_data.title.strip()

    if not title:
        raise HTTPException(
            status_code=422,
            detail="Title cannot be empty",
        )

    document.title = title
    document.updated_at = datetime.now(timezone.utc)
    document.updated_by = user.id

    try:
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not update document",
        )

    return document


# --------------------------------------------------
# 6. Soft-delete a document
# --------------------------------------------------

@router.delete("/{document_id}")
def delete_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    user = get_development_user(db)

    document = (
        db.query(Document)
        .filter(
            Document.id == document_id,
            Document.owner_id == user.id,
            Document.deleted_at.is_(None),
        )
        .first()
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    now = datetime.now(timezone.utc)

    document.deleted_at = now
    document.updated_at = now
    document.updated_by = user.id

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not delete document",
        )

    return {
        "message": "Document deleted successfully",
        "document_id": str(document_id),
    }