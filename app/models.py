from sqlalchemy import Column, Integer, String, Date, Float, UniqueConstraint
from app.core.database import Base


class WeatherRecord(Base):
    """
    Represents a single daily weather observation from a weather station.
    This model is optimized for efficient querying by station and date, which are
    the most common filtering criteria in the API.
    """
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    max_temp = Column(Float, nullable=True)  # Degrees Celsius
    min_temp = Column(Float, nullable=True)  # Degrees Celsius
    precip = Column(Float, nullable=True)   # Stored in mm

    __table_args__ = (
        # A unique constraint on station_id and date is critical for data integrity,
        # preventing duplicate records for the same day at the same station.
        UniqueConstraint('station_id', 'date', name='uix_station_date'),
    )


class WeatherStats(Base):
    """
    Represents the calculated yearly weather statistics for a given station.
    This serves as a materialized view, pre-calculating aggregates to ensure
    fast API responses for statistical queries, avoiding costly on-the-fly computations.
    """
    __tablename__ = "weather_stats"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    avg_max_temp = Column(Float, nullable=True)  # Degrees Celsius
    avg_min_temp = Column(Float, nullable=True)  # Degrees Celsius
    total_precip = Column(Float, nullable=True)  # Stored in cm

    __table_args__ = (
        # Similarly, this constraint ensures that there's only one stats record
        # per station per year.
        UniqueConstraint('station_id', 'year', name='uix_station_year'),
    )
