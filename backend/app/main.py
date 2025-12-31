"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import jobs
from app.config import settings
from app.database.base import init_db
from app.workers.queue import init_queue, shutdown_queue


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize job queue
    init_queue()

    # Re-queue any pending jobs from previous runs
    from app.workers.queue import enqueue_job
    from app.models.job import Job, JobStatus
    from app.database.base import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(Job).where(Job.status == JobStatus.PENDING)
        )
        pending_jobs = result.scalars().all()
        for job in pending_jobs:
            logger.info(f"Re-queueing pending job: {job.id}")
            enqueue_job(job.id)

    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    shutdown_queue()
    logger.info("Application shut down")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix=settings.api_prefix)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    from app.workers.queue import get_queue_size

    return {
        "status": "healthy",
        "queue_size": get_queue_size(),
    }
