#!/bin/bash

# Run FastAPI backend server

cd "$(dirname "$0")"

# Activate virtual environment from parent directory
source ../venv/bin/activate

# Install backend dependencies if needed
pip install -r requirements.txt > /dev/null 2>&1

# Run server
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📖 API docs available at http://localhost:8000/docs"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
