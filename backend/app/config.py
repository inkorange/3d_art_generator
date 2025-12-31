"""Application configuration using Pydantic settings."""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App Info
    app_name: str = "3D Painterly Image Generator API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    storage_dir: Path = base_dir / "storage"
    uploads_dir: Path = storage_dir / "uploads"
    jobs_dir: Path = storage_dir / "jobs"
    outputs_dir: Path = storage_dir / "outputs"
    models_dir: Path = base_dir / "models"
    db_path: Path = storage_dir / "app.db"

    # Database
    @property
    def database_url(self) -> str:
        """Get database URL with absolute path."""
        return f"sqlite+aiosqlite:///{self.db_path}"

    # API Settings
    api_prefix: str = "/api"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    max_upload_size_mb: int = 50

    # Job Queue
    max_concurrent_jobs: int = 1  # For Apple Silicon, process one at a time
    job_timeout_seconds: int = 600  # 10 minutes max

    # ML Pipeline
    ml_pipeline_path: Path = base_dir / "ml_pipeline"
    default_num_layers: int = 4
    default_painterly_strength: float = 0.5
    default_painterly_seed: int = 42

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
settings.uploads_dir.mkdir(parents=True, exist_ok=True)
settings.jobs_dir.mkdir(parents=True, exist_ok=True)
settings.outputs_dir.mkdir(parents=True, exist_ok=True)
