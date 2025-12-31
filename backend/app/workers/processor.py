"""Job processor that runs ML pipelines."""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings
from app.models.job import Job, JobMode, JobStatus


def process_job(job_id: str):
    """Process a generation job.

    This runs in a separate process to isolate ML dependencies.

    Args:
        job_id: Job ID to process
    """
    # Use sync database in worker process
    sync_db_url = f"sqlite:///{settings.db_path}"
    engine = create_engine(sync_db_url)
    db = Session(engine)

    try:
        # Get job
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job not found: {job_id}")
            return

        # Update status to processing
        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        db.commit()

        start_time = time.time()

        # Create output directory
        output_dir = settings.jobs_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        job.output_dir = str(output_dir)
        db.commit()

        # Run appropriate ML pipeline
        if job.mode == JobMode.PHOTO_REALISTIC:
            success, manifest = _run_photorealistic(job, output_dir)
        else:  # JobMode.PAINTERLY
            success, manifest = _run_painterly(job, output_dir)

        processing_time = time.time() - start_time

        if success:
            # Update job as completed
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.processing_time = processing_time
            job.result_manifest = manifest
            logger.info(f"Job {job_id} completed in {processing_time:.2f}s")
        else:
            # Update job as failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.processing_time = processing_time
            logger.error(f"Job {job_id} failed after {processing_time:.2f}s")

        db.commit()

    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)

        # Update job as failed
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update job status: {db_error}")

    finally:
        db.close()


def _run_photorealistic(job: Job, output_dir: Path) -> Tuple[bool, Optional[dict]]:
    """Run photo-realistic pipeline.

    Args:
        job: Job record
        output_dir: Output directory for results

    Returns:
        (success, manifest)
    """
    try:
        logger.info(f"Running photo-realistic pipeline for job {job.id}")

        # Build command
        script_path = settings.ml_pipeline_path / "poc_photorealistic.py"
        cmd = [
            sys.executable,
            str(script_path),
            job.input_path,
            str(job.num_layers),
            str(job.max_size),
        ]

        # Run pipeline
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(settings.base_dir),
            timeout=settings.job_timeout_seconds,
        )

        if result.returncode != 0:
            logger.error(f"Photo-realistic pipeline failed: {result.stderr}")
            return False, None

        # Copy outputs to job output directory
        source_dir = settings.jobs_dir / "photorealistic_test"
        if source_dir.exists():
            for file in source_dir.iterdir():
                if file.is_file():
                    import shutil
                    shutil.copy(file, output_dir / file.name)

        # Read manifest
        manifest_path = output_dir / "layer_manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            return True, manifest

        return True, None

    except subprocess.TimeoutExpired:
        logger.error(f"Photo-realistic pipeline timed out for job {job.id}")
        return False, None
    except Exception as e:
        logger.error(f"Error running photo-realistic pipeline: {e}", exc_info=True)
        return False, None


def _run_painterly(job: Job, output_dir: Path) -> Tuple[bool, Optional[dict]]:
    """Run painterly pipeline.

    Args:
        job: Job record
        output_dir: Output directory for results

    Returns:
        (success, manifest)
    """
    try:
        logger.info(f"Running painterly pipeline for job {job.id}")

        # Build command
        script_path = settings.ml_pipeline_path / "poc_painterly.py"
        cmd = [
            sys.executable,
            str(script_path),
            job.input_path,
            job.painterly_style or "oil painting",
            str(job.painterly_strength or 0.5),
            str(job.painterly_seed or 42),
            str(job.max_size),
        ]

        # Run pipeline
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(settings.base_dir),
            timeout=settings.job_timeout_seconds,
        )

        if result.returncode != 0:
            logger.error(f"Painterly pipeline failed: {result.stderr}")
            return False, None

        # Copy outputs to job output directory
        source_dir = settings.jobs_dir / "poc_test"
        if source_dir.exists():
            for file in source_dir.iterdir():
                if file.is_file():
                    import shutil
                    shutil.copy(file, output_dir / file.name)

        # Create simple manifest for painterly mode (no layers yet)
        manifest = {
            "job_id": job.id,
            "mode": "painterly",
            "style": job.painterly_style,
            "strength": job.painterly_strength,
            "seed": job.painterly_seed,
        }

        return True, manifest

    except subprocess.TimeoutExpired:
        logger.error(f"Painterly pipeline timed out for job {job.id}")
        return False, None
    except Exception as e:
        logger.error(f"Error running painterly pipeline: {e}", exc_info=True)
        return False, None
