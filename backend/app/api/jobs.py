"""Job API endpoints."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.base import get_db
from app.models.job import Job, JobCreate, JobListResponse, JobMode, JobResponse, JobStatus
from app.workers.queue import enqueue_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
) -> dict:
    """Upload an image file for processing.

    Returns the file ID and path for later job creation.
    """
    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image (JPEG, PNG, etc.)",
        )

    # Validate file size
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks
    file_content = bytearray()

    while chunk := await file.read(chunk_size):
        file_size += len(chunk)
        if file_size > settings.max_upload_size_mb * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds {settings.max_upload_size_mb}MB limit",
            )
        file_content.extend(chunk)

    # Generate unique filename
    file_id = str(uuid4())
    file_extension = Path(file.filename or "image.jpg").suffix
    filename = f"{file_id}{file_extension}"
    file_path = settings.uploads_dir / filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)

    return {
        "file_id": file_id,
        "filename": filename,
        "original_filename": file.filename,
        "size_bytes": file_size,
        "path": str(file_path),
    }


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    filename: str = Form(...),
    mode: JobMode = Form(...),
    num_layers: int = Form(default=4),
    max_size: int = Form(default=1024),
    painterly_style: Optional[str] = Form(default="oil painting"),
    painterly_strength: Optional[float] = Form(default=0.5),
    painterly_seed: Optional[int] = Form(default=42),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Create a new generation job.

    Args:
        filename: Uploaded file name (from /upload endpoint)
        mode: Generation mode (photo-realistic or painterly)
        num_layers: Number of depth layers (2-5)
        max_size: Maximum output dimension in pixels (256-2048, default 1024)
                 512 = fast preview, 1024 = balanced, 2048 = high-res
        painterly_style: Style for painterly mode (oil painting, watercolor, etc.)
        painterly_strength: Transformation strength for painterly mode (0.0-1.0)
        painterly_seed: Random seed for painterly mode

    Returns:
        Created job with ID and status
    """
    # Validate uploaded file exists
    file_path = settings.uploads_dir / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Uploaded file not found: {filename}",
        )

    # Validate parameters
    if num_layers < 2 or num_layers > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="num_layers must be between 2 and 5",
        )

    if max_size < 256 or max_size > 2048:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_size must be between 256 and 2048",
        )

    if painterly_strength is not None and (painterly_strength < 0.0 or painterly_strength > 1.0):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="painterly_strength must be between 0.0 and 1.0",
        )

    # Create job record
    job = Job(
        mode=mode,
        input_filename=filename,
        input_path=str(file_path),
        num_layers=num_layers,
        max_size=max_size,
        painterly_style=painterly_style if mode == JobMode.PAINTERLY else None,
        painterly_strength=painterly_strength if mode == JobMode.PAINTERLY else None,
        painterly_seed=painterly_seed if mode == JobMode.PAINTERLY else None,
        status=JobStatus.PENDING,
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Enqueue job for processing
    enqueue_job(job.id)

    # Start processing immediately in a background thread
    import threading
    from app.workers.processor import process_job
    threading.Thread(target=process_job, args=(job.id,), daemon=True).start()

    return JobResponse.model_validate(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """List all jobs with pagination.

    Args:
        skip: Number of jobs to skip
        limit: Maximum number of jobs to return

    Returns:
        List of jobs and total count
    """
    # Get total count
    count_query = select(func.count(Job.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Get jobs
    query = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Get job status and details.

    Args:
        job_id: Job ID

    Returns:
        Job details including status and results
    """
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    return JobResponse.model_validate(job)


@router.api_route("/{job_id}/download/{filename}", methods=["GET", "HEAD"])
async def download_result(
    job_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Download a result file from a completed job.

    Args:
        job_id: Job ID
        filename: File to download (e.g., Layer_1_background.png)

    Returns:
        File download response
    """
    # Get job
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (status: {job.status})",
        )

    if not job.output_dir:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job has no output directory",
        )

    # Validate and get file
    file_path = Path(job.output_dir) / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {filename}",
        )

    # Security check: ensure file is within output directory
    try:
        file_path.resolve().relative_to(Path(job.output_dir).resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="image/png",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a job and its associated files.

    Args:
        job_id: Job ID
    """
    # Get job
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    # Delete output directory if exists
    if job.output_dir and Path(job.output_dir).exists():
        shutil.rmtree(job.output_dir)

    # Delete input file if exists
    if job.input_path and Path(job.input_path).exists():
        Path(job.input_path).unlink()

    # Delete job record
    await db.delete(job)
    await db.commit()
