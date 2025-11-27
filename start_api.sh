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

cd src
python -m uvicorn api.app:app --reload --port 8000 --host 0.0.0.0

