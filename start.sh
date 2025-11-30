#!/bin/bash
set -e

echo "Starting Weather Data Demo Application..."

# Define the database file path
DB_FILE="/app/weather.db"

# Check if the database file already exists (e.g., in a mounted volume)
if [ -f "$DB_FILE" ]; then
    echo "Database file found at $DB_FILE."
else
    echo "Downloading pre-populated database..."
    # Download the database using gdown
    # The ID is extracted from the sharing link: https://drive.google.com/file/d/1BKbtZFIOOCNJJO2_jYaY9Ysz2CwVwVW5/view?usp=sharing
    gdown --id 1BKbtZFIOOCNJJO2_jYaY9Ysz2CwVwVW5 -O "$DB_FILE"
    echo "Database download complete."
fi

echo "Starting web server..."
# Use the PORT environment variable if available (Cloud Run standard), otherwise default to 8080
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}