#!/bin/bash

# Test FastAPI backend with curl

API_BASE="http://localhost:8000/api"

echo "🧪 Testing 3D Painterly Image Generator API"
echo "============================================"
echo ""

# Test 1: Health check
echo "1️⃣  Testing health check..."
curl -s "$API_BASE/../health" | python3 -m json.tool
echo ""
echo ""

# Test 2: Upload image
echo "2️⃣  Uploading test image..."
UPLOAD_RESPONSE=$(curl -s -X POST "$API_BASE/jobs/upload" \
  -F "file=@../storage/uploads/saturn.jpg")
echo "$UPLOAD_RESPONSE" | python3 -m json.tool

FILENAME=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['filename'])")
echo ""
echo "   Uploaded filename: $FILENAME"
echo ""
echo ""

# Test 3: Create photo-realistic job
echo "3️⃣  Creating photo-realistic job..."
JOB_RESPONSE=$(curl -s -X POST "$API_BASE/jobs" \
  -F "filename=$FILENAME" \
  -F "mode=photo-realistic" \
  -F "num_layers=4")
echo "$JOB_RESPONSE" | python3 -m json.tool

JOB_ID=$(echo "$JOB_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo ""
echo "   Job ID: $JOB_ID"
echo ""
echo ""

# Test 4: Poll job status
echo "4️⃣  Polling job status..."
for i in {1..30}; do
    STATUS_RESPONSE=$(curl -s "$API_BASE/jobs/$JOB_ID")
    STATUS=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])")

    echo "   [$i/30] Status: $STATUS"

    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
        echo ""
        echo "   Final job details:"
        echo "$STATUS_RESPONSE" | python3 -m json.tool
        break
    fi

    sleep 2
done
echo ""
echo ""

# Test 5: List jobs
echo "5️⃣  Listing all jobs..."
curl -s "$API_BASE/jobs" | python3 -m json.tool
echo ""
echo ""

echo "✅ API tests complete!"
echo ""
echo "📖 View API docs at: http://localhost:8000/docs"
