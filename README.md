## Project Overview

This project demonstrates data ingestion, modeling, analysis, and API exposure using Python, FastAPI, and SQLAlchemy.

## 🟢 Live Demo

Check out the live application running on Google Cloud Run:
**[Weather Data API & Dashboard](https://weather-crop-data-api-221991611516.europe-west1.run.app/)**

##  Dashboard Preview

Below is a snapshot of the interactive web dashboard. It allows for dynamic filtering by station, year, and date range, and visualizes the data through a combination chart.

![Weather Analytics Dashboard](app/artifacts/snapshot/dashboard_ui.png)

---

## 🚀 Quick Start

Follow these simple instructions to set up and run the project locally.

### Prerequisites
*   Python 3.8+
*   Ensure the `app/artifacts/wx_data` folder (containing the weather text files) is present in the project root directory.

### 1. Setup Environment
```bash
# Install dependencies
pip install -r requirements.txt
```


### 2. Ingest Data (Problem 2)
This script handles data parsing, unit conversion, and duplicate checking. from app/artifacts/wx_data. 
optimized the data processing pipeline to be faster and easier to run.

```bash
python -m app.ingest
```
*   **Optimized Ingestion**: Uses parallel processing (multiprocessing) to parse weather files concurrently, significantly reducing ingestion time.
*   **Efficient Database Inserts**: Implements bulk insert strategies to handle large volumes of data efficiently.
*   **Integrated Workflow**: Automatically triggers the statistical analysis after ingestion is complete.
*   **Action**:
    1.  Ingests data from `app/artifacts/wx_data` into `weather.db`.
    2.  Calculates yearly statistics and updates the `weather_stats` table.
*   **Output**: Detailed progress logs for file processing and database insertion.
*   **Action**: Reads files from `app/artifacts/wx_data`, processes them, and inserts them into the database.
*   **Output**: Console logs indicating start time, number of records processed, and total execution time.
*   **Result**: Creates `weather.db` (SQLite) and populates the `weather_record` table.

### 3. Run Analysis (Problem 3)
Calculate yearly statistics (average max/min temperature, total precipitation) for each weather station.

```bash
python -m app.services.analysis
```
*   **Action**: Aggregates data from `weather_record` and calculates stats.
*   **Result**: Populates the `weather_stats` table with the calculated results.

### 4. Launch REST API (Problem 4)
Start the FastAPI server to expose the data via a REST interface.

```bash
uvicorn app.main:app --reload
```
*   **Web Dashboard**: [http://localhost:8000](http://localhost:8000) (Interactive Data Visualization)
*   **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs) (Interactive API testing)


**Available Endpoints:**
*   `GET /api/weather`: Retrieve raw weather records (supports pagination & filtering).
*   `GET /api/weather/stats`: Retrieve calculated yearly statistics.

### 5. Run Tests
Execute the test suite to verify API functionality and data integrity.

```bash
pytest
```

---

## ☁️ Deployment Strategy

This application is containerized and ready for deployment on serverless container platforms like **Google Cloud Run**.

### Cloud Run "Demo Mode"
For demonstration purposes, the container uses a "Fast Startup" mechanism.

When the container starts:
1.  **Database Download**: Instead of processing raw text files (which is CPU intensive and slow), the container downloads a pre-populated SQLite database (`weather.db`) from a secure remote location.
2.  **Service Start**: The FastAPI web server launches immediately after the download is complete.





### Production Considerations
For a production environment (as outlined in the original architecture plan), the following changes would be made:
*   **Decoupled Pipeline**: Ingestion and analysis would be triggered by events (e.g., file uploads to Cloud Storage/S3) rather than running at container startup.
*   **Persistent Database**: The local SQLite database would be replaced by a managed database service (e.g., Cloud SQL, RDS) to persist data across container restarts.

---

## 🔮 Future Roadmap

While the current implementation fulfills the core requirements, the following enhancements are planned for future iterations:

*   **User Management UI**: Development of a frontend dashboard (using React or Vue.js) allowing users to register, log in, and manage their preferences (e.g., favorite weather stations).
*   **Enhanced Security**: Implementation of OAuth2/JWT authentication to secure API endpoints.