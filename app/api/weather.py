from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import models
from app.schemas import weather as weather_schema
from app.core.database import SessionLocal

router = APIRouter()


def get_db():
    """
    FastAPI dependency that provides a database session for each request.
    This pattern ensures that the session is always closed after the request,
    preventing resource leaks.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/weather", response_model=List[weather_schema.WeatherRecord])
def read_weather_records(
    station_id: str = Query(None, description="Filter by station ID"),
    start_date: date = Query(
        None, description="Start date for filtering (YYYY-MM-DD)"),
    end_date: date = Query(
        None, description="End date for filtering (YYYY-MM-DD)"),
    skip: int = Query(
        0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve weather records with optional filtering and pagination.
    This endpoint directly queries the `weather_records` table and is ideal for
    accessing the raw, daily observations.
    """
    query = db.query(models.WeatherRecord)

    # Dynamically build the query based on the provided filter parameters.
    # This is a clean and efficient way to handle optional filters.
    if station_id:
        query = query.filter(models.WeatherRecord.station_id == station_id)
    if start_date:
        query = query.filter(models.WeatherRecord.date >= start_date)
    if end_date:
        query = query.filter(models.WeatherRecord.date <= end_date)

    # Apply pagination to the result set.
    records = query.offset(skip).limit(limit).all()
    return records


@router.get("/weather/stats", response_model=List[weather_schema.WeatherStats])
def read_weather_stats(
    station_id: str = Query(None, description="Filter by station ID"),
    year: int = Query(None, description="Filter by a specific year"),
    skip: int = Query(
        0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve calculated yearly weather statistics.
    This endpoint queries the `weather_stats` table, which acts as a materialized view.
    This ensures consistently fast response times for statistical data, as the
    aggregations are pre-computed.
    """
    query = db.query(models.WeatherStats)
    if station_id:
        query = query.filter(models.WeatherStats.station_id == station_id)
    if year:
        query = query.filter(models.WeatherStats.year == year)

    stats = query.offset(skip).limit(limit).all()
    return stats


@router.get("/weather/stations", response_model=List[str])
def read_station_ids(db: Session = Depends(get_db)):
    """
    Retrieves a list of all unique weather station IDs available in the dataset.
    This is a useful utility endpoint for clients that need to know which
    stations they can query for.
    """
    # The `distinct()` method ensures that each station ID is returned only once.
    stations = db.query(models.WeatherRecord.station_id).distinct().all()
    # The result from the query is a list of tuples, so we flatten it into a simple list of strings.
    return [station[0] for station in stations]
