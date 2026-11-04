import hashlib
import os
import re
import uuid

from pathlib import Path

from fastapi import HTTPException, UploadFile


# Resolve storage relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]

UPLOAD_DIR = PROJECT_ROOT / "data" / "document_uploads"

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".md",
    ".txt",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def sanitize_filename(filename: str | None) -> str:
    """
    Return a safe display filename.
    Never use this filename as the storage path.
    """

    if not filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    # Handle both Unix and Windows path separators.
    filename = filename.replace("\\", "/").split("/")[-1]

    filename = filename.replace("\x00", "")

    filename = re.sub(
        r"[\x00-\x1f\x7f]",
        "",
        filename,
    )

    filename = filename.strip()

    if not filename or filename in {".", ".."}:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    if len(filename) > 500:
        raise HTTPException(
            status_code=400,
            detail="Filename is too long",
        )

    return filename


async def save_uploaded_file(file: UploadFile):
    """
    Stream an upload to a UUID-based path.

    Returns:
        storage_path
        original_filename
        extension
        file_size
        checksum
    """

    original_filename = sanitize_filename(file.filename)

    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file extension",
        )

    document_id = uuid.uuid4()

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Use UUID-based storage.
    # Never construct the destination from the original filename.
    destination = UPLOAD_DIR / f"{document_id}{extension}"

    size = 0
    checksum = hashlib.sha256()

    try:
        with destination.open("xb") as output:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                size += len(chunk)

                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="File exceeds the 20 MB limit",
                    )

                checksum.update(chunk)
                output.write(chunk)

        if size == 0:
            raise HTTPException(
                status_code=400,
                detail="Empty files are not allowed",
            )

        return {
            "id": document_id,
            "storage_path": str(destination),
            "original_filename": original_filename,
            "extension": extension,
            "file_size_bytes": size,
            "file_checksum": checksum.hexdigest(),
        }

    except Exception:
        # Remove incomplete files.
        destination.unlink(missing_ok=True)
        raise

    finally:
        await file.close()