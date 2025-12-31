# NPM Scripts Reference

Root-level package.json scripts for managing the full-stack application.

## Development Scripts

### `npm run dev`
**Start both backend and frontend in development mode**

Runs both services concurrently in a single terminal:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

```bash
npm run dev
```

**Output:**
```
[0] 🚀 Starting FastAPI server on http://localhost:8000
[1] ▲ Next.js 15.1.1
[1] - Local:        http://localhost:3000
```

Press `Ctrl+C` to stop both services.

---

### `npm run dev:backend`
**Start only the backend**

```bash
npm run dev:backend
```

Equivalent to:
```bash
cd backend && ./run.sh
```

---

### `npm run dev:frontend`
**Start only the frontend**

```bash
npm run dev:frontend
```

Equivalent to:
```bash
cd frontend && npm run dev
```

---

## Production Scripts

### `npm run build:frontend`
**Build frontend for production**

```bash
npm run build:frontend
```

Creates optimized production build in `frontend/.next/`

---

### `npm start`
**Start both services in production mode**

```bash
npm run build:frontend  # Build first
npm start               # Then start both
```

Runs:
- Backend: Production uvicorn server
- Frontend: Next.js production server

---

### `npm run start:backend`
**Start only backend in production mode**

```bash
npm run start:backend
```

---

### `npm run start:frontend`
**Start only frontend in production mode**

```bash
npm run start:frontend
```

---

## Installation Scripts

### `npm run install:all`
**Install all dependencies (backend + frontend)**

```bash
npm run install:all
```

Runs both:
- `npm run install:backend`
- `npm run install:frontend`

Use this for first-time setup!

---

### `npm run install:backend`
**Install backend Python dependencies**

```bash
npm run install:backend
```

Installs from `backend/requirements.txt` into the virtual environment.

---

### `npm run install:frontend`
**Install frontend Node dependencies**

```bash
npm run install:frontend
```

Installs from `frontend/package.json`.

---

## Testing Scripts

### `npm run test:api`
**Run backend API tests**

```bash
npm run test:api
```

Runs the backend test script:
1. Health check
2. Image upload
3. Job creation
4. Status polling
5. Job listing

---

## First-Time Setup

```bash
# 1. Install concurrently (root package)
npm install

# 2. Install all project dependencies
npm run install:all

# 3. Start development servers
npm run dev
```

---

## Common Workflows

### Daily Development
```bash
npm run dev
# Open http://localhost:3000
```

### Testing Backend API
```bash
npm run dev:backend          # Terminal 1
npm run test:api             # Terminal 2
```

### Production Deployment
```bash
npm run install:all
npm run build:frontend
npm start
```

### Install New Backend Dependency
```bash
cd backend
source ../venv/bin/activate
pip install package-name
pip freeze > requirements.txt
```

### Install New Frontend Dependency
```bash
cd frontend
npm install package-name
```

---

## Troubleshooting

### Port already in use

**Backend (8000):**
```bash
lsof -ti:8000 | xargs kill -9
npm run dev:backend
```

**Frontend (3000):**
```bash
lsof -ti:3000 | xargs kill -9
npm run dev:frontend
```

### Backend won't start

```bash
npm run install:backend
npm run dev:backend
```

### Frontend won't start

```bash
npm run install:frontend
npm run dev:frontend
```

### Clean restart

```bash
# Kill all Node processes
killall node

# Kill backend if running
lsof -ti:8000 | xargs kill -9

# Restart
npm run dev
```

---

## Environment Variables

### Backend
Edit `backend/.env` (optional):
```env
API_PREFIX=/api
MAX_UPLOAD_SIZE_MB=50
```

### Frontend
Edit `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

---

## Notes

- **concurrently**: Runs multiple commands in parallel
- **Backend**: Uses Python uvicorn server
- **Frontend**: Uses Next.js dev server
- **Logs**: Color-coded output ([0] = backend, [1] = frontend)
- **Stop**: `Ctrl+C` stops all services
