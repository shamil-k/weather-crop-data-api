from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app import models
from app.schemas import weather as weather_schema
from app.core.database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/weather", response_model=List[weather_schema.WeatherRecord])
def read_weather_records(
    station_id: str = Query(None, description="Filter by station ID"),
    start_date: date = Query(None, description="Start date for filtering"),
    end_date: date = Query(None, description="End date for filtering"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(models.WeatherRecord)
    if station_id:
        query = query.filter(models.WeatherRecord.station_id == station_id)
    if start_date:
        query = query.filter(models.WeatherRecord.date >= start_date)
    if end_date:
        query = query.filter(models.WeatherRecord.date <= end_date)

    records = query.offset(skip).limit(limit).all()
    return records


@router.get("/weather/stats", response_model=List[weather_schema.WeatherStats])
def read_weather_stats(
    station_id: str = Query(None, description="Filter by station ID"),
    year: int = Query(None, description="Filter by year"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
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
    Retrieves a list of unique weather station IDs.
    """
    stations = db.query(models.WeatherRecord.station_id).distinct().all()
    return [station[0] for station in stations]
