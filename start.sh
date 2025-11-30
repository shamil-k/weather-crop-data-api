#!/bin/bash
set -e

echo "Starting Weather Data Demo Application..."

# Initialize database tables first
echo "Initializing database..."
python -c "from app.core.database import engine; from app.models import Base; Base.metadata.create_all(bind=engine)"
echo "Database initialized."

# Function to run data pipeline in the background
run_pipeline() {
    echo "Starting background data pipeline..."
    
    # Enable sequential mode for Cloud Run to avoid /dev/shm issues
    export SEQUENTIAL_INGEST=true
    
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