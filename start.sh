#!/bin/bash
set -e

echo "Starting Weather Data Demo Application..."

# Function to run data pipeline in the background
run_pipeline() {
    echo "Starting background data pipeline..."
    echo "[1/2] Starting data ingestion..."
    python -m app.ingest
    echo "Data ingestion complete."

    echo "[2/2] Starting analysis..."
    python -m app.services.analysis
    echo "Analysis complete."
    echo "Background pipeline finished successfully."
}

# Start the pipeline in the background so the web server can start immediately
# This prevents Cloud Run from killing the container due to startup timeout
run_pipeline &

echo "Starting web server..."
# Use the PORT environment variable if available (Cloud Run standard), otherwise default to 8080
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}