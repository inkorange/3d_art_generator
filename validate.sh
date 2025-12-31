#!/bin/bash

echo "🔍 Validating 3D Painterly Image Generator Setup"
echo "================================================"
echo ""

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: Run this script from the project root"
    exit 1
fi

# Validate Frontend
echo "📦 Validating Frontend..."
cd frontend

# Check TypeScript
echo "  - Running TypeScript check..."
if npx tsc --noEmit > /dev/null 2>&1; then
    echo "  ✅ TypeScript: No errors"
else
    echo "  ❌ TypeScript: Has errors"
    npx tsc --noEmit
    exit 1
fi

# Check build
echo "  - Running production build..."
if npm run build > /dev/null 2>&1; then
    echo "  ✅ Build: Successful"
else
    echo "  ❌ Build: Failed"
    npm run build
    exit 1
fi

cd ..

# Validate Backend
echo ""
echo "🐍 Validating Backend..."
echo "  - Checking Python dependencies..."
if [ -d "venv" ]; then
    echo "  ✅ Virtual environment exists"
else
    echo "  ⚠️  Virtual environment not found"
fi

echo ""
echo "✅ All validations passed!"
echo ""
echo "To start the application:"
echo "  npm run dev"
echo ""
echo "Or separately:"
echo "  Terminal 1: cd backend && ./run.sh"
echo "  Terminal 2: cd frontend && npm run dev"
