# Backend API - 3D Painterly Image Generator

FastAPI backend with job queue for photo-realistic and painterly image generation.

## Features

- ✅ RESTful API with FastAPI
- ✅ Async SQLite database with SQLAlchemy
- ✅ Simple job queue using Python multiprocessing
- ✅ File upload handling (max 50MB)
- ✅ Job status tracking (pending, processing, completed, failed)
- ✅ Dual mode support (photo-realistic & painterly)
- ✅ Result download endpoints
- ✅ CORS support for Next.js frontend
- ✅ Auto-generated API documentation (Swagger/OpenAPI)

## Quick Start

### 1. Install Dependencies

```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Server

```bash
./run.sh
```

Server will start on `http://localhost:8000`

- API Base: `http://localhost:8000/api`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 3. Test API

```bash
./test_api.sh
```

## API Endpoints

### Health & Status

- `GET /` - API info
- `GET /health` - Health check with queue status

### Jobs

- `POST /api/jobs/upload` - Upload image file
- `POST /api/jobs` - Create generation job
- `GET /api/jobs` - List all jobs (with pagination)
- `GET /api/jobs/{id}` - Get job details
- `GET /api/jobs/{id}/download/{filename}` - Download result file
- `DELETE /api/jobs/{id}` - Delete job and files

## Usage Examples

### 1. Upload Image

```bash
curl -X POST http://localhost:8000/api/jobs/upload \
  -F "file=@path/to/image.jpg"
```

Response:
```json
{
  "file_id": "uuid",
  "filename": "uuid.jpg",
  "original_filename": "image.jpg",
  "size_bytes": 123456,
  "path": "/path/to/uploads/uuid.jpg"
}
```

### 2. Create Photo-Realistic Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "filename=uuid.jpg" \
  -F "mode=photo-realistic" \
  -F "num_layers=4"
```

### 3. Create Painterly Job

```bash
curl -X POST http://localhost:8000/api/jobs \
  -F "filename=uuid.jpg" \
  -F "mode=painterly" \
  -F "num_layers=4" \
  -F "painterly_style=oil painting" \
  -F "painterly_strength=0.5" \
  -F "painterly_seed=42"
```

### 4. Get Job Status

```bash
curl http://localhost:8000/api/jobs/{job_id}
```

Response:
```json
{
  "id": "uuid",
  "status": "completed",
  "mode": "photo-realistic",
  "num_layers": 4,
  "input_filename": "uuid.jpg",
  "output_dir": "/path/to/jobs/uuid",
  "result_manifest": {
    "job_id": "uuid",
    "layer_count": 4,
    "layers": [...]
  },
  "created_at": "2024-12-28T10:00:00",
  "completed_at": "2024-12-28T10:00:05",
  "processing_time": 5.7
}
```

### 5. Download Result

```bash
curl -O http://localhost:8000/api/jobs/{job_id}/download/Layer_1_background.png
```

### 6. List All Jobs

```bash
curl http://localhost:8000/api/jobs?skip=0&limit=10
```

## Job Statuses

- `pending` - Job created, waiting in queue
- `processing` - Job currently being processed
- `completed` - Job finished successfully
- `failed` - Job encountered an error
- `cancelled` - Job was cancelled (future feature)

## Configuration

Edit `app/config.py` or create `.env` file:

```env
# API Settings
API_PREFIX=/api
CORS_ORIGINS=["http://localhost:3000"]
MAX_UPLOAD_SIZE_MB=50

# Job Queue
MAX_CONCURRENT_JOBS=1
JOB_TIMEOUT_SECONDS=600

# ML Pipeline
DEFAULT_NUM_LAYERS=4
DEFAULT_PAINTERLY_STRENGTH=0.5
DEFAULT_PAINTERLY_SEED=42
```

## Architecture

```
backend/
├── app/
│   ├── api/
│   │   └── jobs.py              # Job endpoints
│   ├── database/
│   │   └── base.py              # Database setup
│   ├── models/
│   │   └── job.py               # Job model & schemas
│   ├── workers/
│   │   ├── queue.py             # Job queue
│   │   └── processor.py         # ML pipeline integration
│   ├── config.py                # Configuration
│   └── main.py                  # FastAPI app
├── requirements.txt             # Python dependencies
├── run.sh                       # Start server script
└── test_api.sh                  # API test script
```

## Database Schema

### Job Table

| Column | Type | Description |
|--------|------|-------------|
| id | String | UUID primary key |
| status | Enum | Job status |
| mode | Enum | photo-realistic or painterly |
| input_filename | String | Uploaded file name |
| input_path | String | File path |
| num_layers | Integer | Number of depth layers (2-5) |
| painterly_style | String | Style for painterly mode |
| painterly_strength | Float | Strength for painterly mode (0.0-1.0) |
| painterly_seed | Integer | Seed for painterly mode |
| output_dir | String | Job output directory |
| result_manifest | JSON | Layer manifest |
| error_message | Text | Error details if failed |
| created_at | DateTime | Job creation time |
| started_at | DateTime | Processing start time |
| completed_at | DateTime | Processing end time |
| processing_time | Float | Total processing time (seconds) |

## Job Queue

- Simple Python multiprocessing queue
- Processes one job at a time (configured for Apple Silicon)
- 10-minute timeout per job
- Automatic retry on worker crash (future feature)

## Error Handling

All API errors return standard HTTP status codes with JSON error messages:

```json
{
  "detail": "Error message here"
}
```

Common errors:
- `400 Bad Request` - Invalid parameters
- `404 Not Found` - Job or file not found
- `413 Payload Too Large` - File exceeds 50MB
- `500 Internal Server Error` - Server error

## Development

### Run in Development Mode

```bash
cd backend
source ../venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### View Logs

Logs are printed to console with loguru formatting.

### Database Location

SQLite database: `storage/app.db`

To reset database:
```bash
rm storage/app.db
# Restart server - will recreate tables
```

## Next Steps (Phase 3)

- [ ] Add WebSocket support for real-time job updates
- [ ] Implement batch job creation
- [ ] Add job cancellation
- [ ] Implement job priority queue
- [ ] Add Redis support for production deployment
- [ ] Add rate limiting
- [ ] Add authentication/API keys
- [ ] Add result caching

## Integration with Phase 1 ML Pipelines

The backend integrates with Phase 1 ML scripts:
- `ml_pipeline/poc_photorealistic.py` - Photo-realistic mode
- `ml_pipeline/poc_painterly.py` - Painterly mode

Jobs are processed in isolated Python processes to prevent ML dependency conflicts.
