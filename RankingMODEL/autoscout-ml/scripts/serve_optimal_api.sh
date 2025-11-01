#!/bin/bash

# Serve the optimal AutoScout24 ML API

echo "🚀 Starting Optimal AutoScout24 ML API"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "src/api_optimal.py" ]; then
    echo "❌ Error: Please run this script from the autoscout-ml directory"
    exit 1
fi

# Check if model exists
if [ ! -f "artifacts/model_optimal.cbm" ]; then
    echo "❌ Error: Optimal model not found. Please run:"
    echo "   python scripts/train_optimal_model.py"
    exit 1
fi

# Check if precomputed data exists
if [ ! -f "data/precomputed_optimal.parquet" ]; then
    echo "⚠️  Warning: Optimal precomputed data not found."
    echo "   Run: python scripts/precompute_scores_optimal.py"
    echo "   Continuing with fallback data..."
fi

echo "🌐 Starting API server..."
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the API server
python -m uvicorn src.api_optimal:app --host 0.0.0.0 --port 8000 --reload
