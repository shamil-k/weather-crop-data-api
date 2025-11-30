#!/bin/bash
set -e

echo "Starting Weather Data Demo Application..."

echo "[1/3] Starting data ingestion..."
python -m app.ingest
echo "Data ingestion complete."

echo "[2/3] Starting analysis..."
python -m app.services.analysis
echo "Analysis complete."

echo "[3/3] Starting web server..."
# Use the PORT environment variable if available (Cloud Run standard), otherwise default to 80
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-80}