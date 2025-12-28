# 3D Painterly Image Generator

A local software tool that generates high-definition 3D painterly images from photo references, suitable for print production. Uses depth estimation, generative AI, and controlled randomness to create unique artistic interpretations with depth layer separation for physical 3D assembly.

## Project Status

**Phase 1: Foundation & Proof of Concept** ✅ **COMPLETE**

See [TEST_RESULTS.md](TEST_RESULTS.md) for comprehensive test results and performance benchmarks.

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3)
- Python 3.9+
- 20GB free disk space
- 16GB RAM

### Installation

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
├── venv/                  # Python virtual environment
├── ml_pipeline/           # ML generation scripts
│   ├── poc_painterly.py  # Phase 1 proof-of-concept
│   └── README.md         # ML pipeline documentation
├── models/                # Downloaded ML models (auto-created)
├── storage/               # Data storage
│   ├── uploads/          # Input images
│   ├── jobs/             # Job working directories
│   └── outputs/          # Final outputs
├── requirements.txt       # Python dependencies
├── test_setup.py         # Environment validation
└── README.md             # This file
```

## Features

### Implemented ✅
- ✅ Photo to painterly image conversion
- ✅ Depth map generation (MiDaS DPT)
- ✅ **Dual Mode Support:**
  - ✅ Photo-Realistic (preserves original photo, 5.7s avg)
  - ✅ Painterly (AI transformation, 49.9s avg)
- ✅ Depth layer separation (3 layers with alpha transparency + feathering)
- ✅ Layer manifest JSON export
- ✅ Reproducible results (seed-controlled)

### Planned 🚧
- 🚧 FastAPI backend & job queue
- 🚧 Next.js web UI
- 🚧 Multiple style presets (oil, watercolor, palette knife)
- 🚧 High-resolution upscaling (300-600 DPI)
- 🚧 Batch generation (1-3 variations)
- 🚧 Settings persistence
- 🚧 Advanced layer separation (k-means, 2-5 variable layers)

## Documentation

- [PROJECT.md](.claude/PROJECT.md) - Complete project plan and architecture
- [TEST_RESULTS.md](TEST_RESULTS.md) - Phase 1 test results and benchmarks
- [ML Pipeline README](ml_pipeline/README.md) - Phase 1 documentation

## Development Phases

- [x] **Phase 1**: Foundation & Proof of Concept (Current)
- [ ] **Phase 2**: Backend API & Job Queue
- [ ] **Phase 3**: Frontend UI
- [ ] **Phase 4**: Depth Layer Separation
- [ ] **Phase 5**: Advanced ML Features
- [ ] **Phase 6**: High-Resolution Pipeline
- [ ] **Phase 7**: Polish & Optimization
- [ ] **Phase 8**: Advanced 3D Features (Optional)

## License

Personal project - not for public distribution
