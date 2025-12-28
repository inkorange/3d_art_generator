# 3D Painterly Image Generator

A local software tool that generates high-definition 3D painterly images from photo references, suitable for print production. Uses depth estimation, generative AI, and controlled randomness to create unique artistic interpretations with depth layer separation for physical 3D assembly.

## Project Status

**Phase 1: Foundation & Proof of Concept** ✅ **COMPLETE**
**Phase 2: Backend API & Job Queue** ✅ **COMPLETE**

See [TEST_RESULTS.md](TEST_RESULTS.md) for Phase 1 test results and [backend/README.md](backend/README.md) for API documentation.

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.9+
- 20GB free disk space
- 16GB RAM

### Option 1: Use Backend API (Recommended)

```bash
# 1. Start FastAPI backend
cd backend
./run.sh
```

Server runs on `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Test API: `./backend/test_api.sh`

See [backend/README.md](backend/README.md) for full API documentation.

### Option 2: Direct ML Pipeline

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Test setup
python test_setup.py

# 3. Run proof-of-concept (will download models on first run)
python ml_pipeline/poc_painterly.py storage/uploads/test_landscape.jpg
```

### First Run Notes

- Models will download automatically (~4-5GB)
- Download may take 5-10 minutes
- Subsequent runs are much faster
- Generation takes ~1 minute per image on Apple Silicon

## Project Structure

```
3d_art_generator/
├── .claude/                # Project configuration
│   ├── claude.json        # Claude project config
│   └── PROJECT.md         # Detailed project plan
├── backend/                # FastAPI backend (Phase 2)
│   ├── app/               # Application code
│   │   ├── api/          # API endpoints
│   │   ├── database/     # Database setup
│   │   ├── models/       # Data models
│   │   ├── workers/      # Job queue & processor
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt   # Backend dependencies
│   ├── run.sh            # Start server script
│   ├── test_api.sh       # API test script
│   └── README.md         # API documentation
├── venv/                  # Python virtual environment
├── ml_pipeline/           # ML generation scripts
│   ├── poc_painterly.py  # Painterly mode
│   ├── poc_photorealistic.py  # Photo-realistic mode
│   └── README.md         # ML pipeline documentation
├── models/                # Downloaded ML models (auto-created)
├── storage/               # Data storage
│   ├── uploads/          # Input images
│   ├── jobs/             # Job working directories
│   ├── outputs/          # Final outputs
│   └── app.db            # SQLite database (auto-created)
├── requirements.txt       # ML pipeline dependencies
├── test_setup.py         # Environment validation
└── README.md             # This file
```

## Features

### Implemented ✅

**Phase 1: ML Pipeline**
- ✅ Photo to painterly image conversion (SD 1.5)
- ✅ Depth map generation (MiDaS DPT)
- ✅ **Dual Mode Support:**
  - ✅ Photo-Realistic (preserves original photo, 5.7s avg)
  - ✅ Painterly (AI transformation with enhanced effect, ~40s avg)
- ✅ Adaptive depth layer separation (2-5 layers, percentile-based)
- ✅ Opaque background layer with smooth blurred fallback
- ✅ Alpha feathering (2px + 21px blend for background)
- ✅ Layer manifest JSON export
- ✅ Reproducible results (seed-controlled)

**Phase 2: Backend API**
- ✅ RESTful API with FastAPI
- ✅ File upload handling (max 50MB)
- ✅ Job queue with multiprocessing
- ✅ Async SQLite database
- ✅ Job status tracking (pending, processing, completed, failed)
- ✅ Result download endpoints
- ✅ CORS support for frontend
- ✅ Auto-generated API docs (Swagger/OpenAPI)

### Planned 🚧
- 🚧 Next.js web UI
- 🚧 Multiple style presets (oil, watercolor, palette knife)
- 🚧 High-resolution upscaling (300-600 DPI)
- 🚧 Batch generation (1-3 variations)
- 🚧 Settings persistence
- 🚧 WebSocket real-time updates

## Documentation

- [PROJECT.md](.claude/PROJECT.md) - Complete project plan and architecture
- [TEST_RESULTS.md](TEST_RESULTS.md) - Phase 1 test results and benchmarks
- [ML Pipeline README](ml_pipeline/README.md) - Phase 1 ML documentation
- [Backend API README](backend/README.md) - Phase 2 API documentation
- [OPAQUE_BACKGROUND_FEATURE.md](OPAQUE_BACKGROUND_FEATURE.md) - Opaque background implementation
- [LAYER_SEPARATION_RESULTS.md](LAYER_SEPARATION_RESULTS.md) - Adaptive layer separation results

## Development Phases

- [x] **Phase 1**: Foundation & Proof of Concept ✅ COMPLETE
- [x] **Phase 2**: Backend API & Job Queue ✅ COMPLETE
- [ ] **Phase 3**: Frontend UI (Next)
- [ ] **Phase 4**: Advanced Layer Features
- [ ] **Phase 5**: Advanced ML Features
- [ ] **Phase 6**: High-Resolution Pipeline
- [ ] **Phase 7**: Polish & Optimization
- [ ] **Phase 8**: Advanced 3D Features (Optional)

## License

Personal project - not for public distribution
