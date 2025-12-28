"""Simple job queue using Python multiprocessing.

This is a lightweight queue suitable for local-only deployment.
For production, consider using Dramatiq with Redis or RabbitMQ.
"""

import multiprocessing
import queue
import threading
from typing import Optional

from loguru import logger

from app.config import settings

# Global queue and worker thread
_job_queue: Optional[queue.Queue] = None
_worker_thread: Optional[threading.Thread] = None
_shutdown_event = threading.Event()


def init_queue():
    """Initialize the job queue and worker thread."""
    global _job_queue, _worker_thread

    if _job_queue is not None:
        logger.warning("Job queue already initialized")
        return

    logger.info("Initializing job queue")
    _job_queue = queue.Queue(maxsize=100)

    # Start worker thread
    _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
    _worker_thread.start()

    logger.info("Job queue initialized")


def shutdown_queue():
    """Shutdown the job queue gracefully."""
    global _job_queue, _worker_thread

    if _job_queue is None:
        return

    logger.info("Shutting down job queue")
    _shutdown_event.set()

    if _worker_thread and _worker_thread.is_alive():
        _worker_thread.join(timeout=5)

    _job_queue = None
    _worker_thread = None
    logger.info("Job queue shut down")


def enqueue_job(job_id: str):
    """Add a job to the processing queue.

    Args:
        job_id: Job ID to process
    """
    if _job_queue is None:
        raise RuntimeError("Job queue not initialized. Call init_queue() first.")

    try:
        _job_queue.put(job_id, block=False)
        logger.info(f"Enqueued job: {job_id}")
    except queue.Full:
        logger.error(f"Job queue is full, cannot enqueue job: {job_id}")
        raise RuntimeError("Job queue is full. Please try again later.")


def _worker_loop():
    """Worker thread that processes jobs from the queue."""
    from app.workers.processor import process_job

    logger.info("Worker thread started")

    while not _shutdown_event.is_set():
        try:
            # Get job from queue with timeout
            job_id = _job_queue.get(timeout=1.0)

            logger.info(f"Processing job: {job_id}")

            # Process job in a separate process to isolate ML dependencies
            process = multiprocessing.Process(target=process_job, args=(job_id,))
            process.start()
            process.join(timeout=settings.job_timeout_seconds)

            if process.is_alive():
                logger.error(f"Job {job_id} timed out after {settings.job_timeout_seconds}s")
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()

            logger.info(f"Finished processing job: {job_id}")

        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Error in worker loop: {e}", exc_info=True)
            continue

    logger.info("Worker thread stopped")


def get_queue_size() -> int:
    """Get the current number of jobs in the queue."""
    if _job_queue is None:
        return 0
    return _job_queue.qsize()
