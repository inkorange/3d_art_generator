# Quick Start Guide

## Start the Application

### Option 1: Start Both Services at Once (Recommended)

From the project root:

```bash
npm run dev
```

This starts both backend and frontend in a single terminal!

### Option 2: Start Services Separately

**Terminal 1 - Backend:**
```bash
cd backend
./run.sh
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Open Your Browser

Visit: `http://localhost:3000`

You should see:
- ✅ Backend running on `http://localhost:8000`
- ✅ Frontend running on `http://localhost:3000`

---

## Using the Application

1. **Upload an image**
   - Drag & drop or click to select
   - Max 50MB, any image format

2. **Choose mode**
   - **Photo-Realistic**: Fast (5-7s), preserves original photo
   - **Painterly**: Slower (40s), AI artistic transformation

3. **Adjust parameters**
   - Layers: 2-5 (for 3D depth effect)
   - For Painterly mode:
     - Style: oil painting, watercolor, etc.
     - Strength: how much to transform (0-1)
     - Seed: for reproducible results

4. **Click "Generate"**
   - Watch the progress
   - See elapsed time

5. **Download results**
   - Preview individual layers
   - Download all files
   - Generate another image

---

## Troubleshooting

### "Cannot connect to backend" error

**Solution:** Make sure the backend is running in a separate terminal:
```bash
cd backend
./run.sh
```

### Backend won't start

**Check dependencies:**
```bash
cd backend
source ../venv/bin/activate
pip install -r requirements.txt
```

### Frontend won't start

**Install dependencies:**
```bash
cd frontend
npm install
```

### Port already in use

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
```

**Frontend (3000):**
```bash
lsof -ti:3000 | xargs kill -9
```

---

## API Endpoints

- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

---

## First Time Setup

If this is your first time running the application:

1. **Python virtual environment** (if not created):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Backend dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```

4. **ML Models** will download automatically (~4-5GB) on first generation

---

## Performance Notes

- **Photo-Realistic mode**: ~5-7 seconds
- **Painterly mode**: ~40 seconds
- **First run**: Longer due to model downloads
- **Subsequent runs**: Much faster (models cached)

---

## Need Help?

- Frontend docs: [frontend/README.md](frontend/README.md)
- Backend docs: [backend/README.md](backend/README.md)
- Phase 1 results: [TEST_RESULTS.md](TEST_RESULTS.md)
- Phase 2 completion: [PHASE_2_COMPLETE.md](PHASE_2_COMPLETE.md)
- Phase 3 completion: [PHASE_3_COMPLETE.md](PHASE_3_COMPLETE.md)
