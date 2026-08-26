from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.processing_job import ProcessingJob
from app.schemas.processing_job import (
    ProcessingJobCreate,
    ProcessingJobResponse,
)


router = APIRouter(
    prefix="/processing-jobs",
    tags=["Processing Jobs"],
)


@router.post("/", response_model=ProcessingJobResponse)
def create_processing_job(
    data: ProcessingJobCreate,
    db: Session = Depends(get_db),
):
    job = ProcessingJob(
        **data.model_dump()
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


@router.get("/", response_model=list[ProcessingJobResponse])
def list_processing_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(ProcessingJob)
        .order_by(ProcessingJob.created_at.desc())
        .all()
    )


@router.get("/{job_id}", response_model=ProcessingJobResponse)
def get_processing_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found",
        )

    return job


@router.put("/{job_id}", response_model=ProcessingJobResponse)
def update_processing_job(
    job_id: UUID,
    data: ProcessingJobCreate,
    db: Session = Depends(get_db),
):
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found",
        )

    for key, value in data.model_dump().items():
        setattr(job, key, value)

    db.commit()
    db.refresh(job)

    return job


@router.delete("/{job_id}")
def delete_processing_job(
    job_id: UUID,
    db: Session = Depends(get_db),
):
    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Processing job not found",
        )

    db.delete(job)
    db.commit()

    return {
        "message": "Processing job deleted successfully",
        "job_id": job_id,
    }