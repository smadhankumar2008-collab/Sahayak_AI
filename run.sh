#!/bin/bash
# Sahayak AI - Quick Start Script

echo "🌾 Sahayak AI - Cooperative Compliance Co-Pilot"
echo "================================================"

# Check if data exists, if not ingest
if [ ! -f "backend/data/vector_store.faiss" ]; then
    echo "📚 Knowledge base not ingested, running ingestion..."
    python scripts/ingest.py --max-urls 0
fi

echo "🚀 Starting backend on http://localhost:8000"
echo "📱 Frontend available at http://localhost:8000/app"
echo ""
echo "Press Ctrl+C to stop"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
