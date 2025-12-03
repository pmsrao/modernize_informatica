#!/bin/bash
# Quick script to start the API server

echo "Starting Informatica Modernization API..."
echo ""

# Check if we're in the right directory
if [ ! -d "src" ]; then
    echo "Error: src directory not found. Please run from project root."
    exit 1
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "uvicorn not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the API
echo "Starting API on http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Set PYTHONPATH to include both project root (for ai_agents) and src (for other imports)
export PYTHONPATH="${PYTHONPATH}:$(pwd):$(pwd)/src"

# Load environment variables from .env file if it exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Set ENABLE_GRAPH_STORE if not already set (default to true for graph store features)
export ENABLE_GRAPH_STORE="${ENABLE_GRAPH_STORE:-true}"

# Run from project root
python -m uvicorn api.app:app --reload --port 8000 --host 0.0.0.0

