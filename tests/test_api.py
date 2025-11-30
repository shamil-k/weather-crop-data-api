import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date

from app.main import app
from app.core.database import Base
from app.api.weather import get_db
from app.models import WeatherRecord, WeatherStats

# Use a dedicated SQLite file for testing
TEST_DB_PATH = "./test_weather.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={
                       "check_same_thread": False})
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_and_teardown_db():
    # Setup: create db and tables
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    Base.metadata.create_all(bind=engine)

    # Yield control to the test session
    yield

    # Teardown: close connections and remove db file
    engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(scope="function")
def db_session_with_data():
    db = TestingSessionLocal()
    try:
        # Clear existing data
        db.query(WeatherRecord).delete()
        db.query(WeatherStats).delete()
        db.commit()

        # Populate with fresh sample data for each test
        db.add(WeatherRecord(station_id="TEST01", date=date(
            2022, 1, 1), max_temp=10.0, min_temp=0.0, precip=5.0))
        db.add(WeatherRecord(station_id="TEST01", date=date(
            2022, 1, 2), max_temp=12.0, min_temp=2.0, precip=0.0))
        db.add(WeatherRecord(station_id="TEST02", date=date(
            2022, 1, 1), max_temp=15.0, min_temp=5.0, precip=1.0))

        db.add(WeatherStats(station_id="TEST01", year=2022,
               avg_max_temp=11.0, avg_min_temp=1.0, total_precip=0.5))
        db.add(WeatherStats(station_id="TEST02", year=2022,
               avg_max_temp=15.0, avg_min_temp=5.0, total_precip=0.1))

        db.commit()
        yield db
    finally:
        db.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_read_weather_records_all(db_session_with_data):
    response = client.get("/api/weather")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["station_id"] == "TEST01"


def test_read_weather_records_filter_by_station(db_session_with_data):
    response = client.get("/api/weather?station_id=TEST02")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["station_id"] == "TEST02"


def test_read_weather_records_filter_by_date(db_session_with_data):
    response = client.get("/api/weather?start_date=2022-01-02")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["date"] == "2022-01-02"


def test_read_weather_stats_all(db_session_with_data):
    response = client.get("/api/weather/stats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["avg_max_temp"] == 11.0


def test_read_weather_stats_filter_by_year_and_station(db_session_with_data):
    response = client.get("/api/weather/stats?station_id=TEST02&year=2022")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["station_id"] == "TEST02"
    assert data[0]["year"] == 2022


def test_read_station_ids(db_session_with_data):
    response = client.get("/api/weather/stations")
    assert response.status_code == 200
    data = response.json()
    assert sorted(data) == ["TEST01", "TEST02"]
