from sqlalchemy import Column, Integer, String, Date, Float, UniqueConstraint
from app.core.database import Base


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True, nullable=False)
    date = Column(Date, index=True, nullable=False)
    max_temp = Column(Float, nullable=True)  # Degrees Celsius
    min_temp = Column(Float, nullable=True)  # Degrees Celsius
    precip = Column(Float, nullable=True)   # mm

    __table_args__ = (
        UniqueConstraint('station_id', 'date', name='uix_station_date'),
    )


class WeatherStats(Base):
    __tablename__ = "weather_stats"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String, index=True, nullable=False)
    year = Column(Integer, index=True, nullable=False)
    avg_max_temp = Column(Float, nullable=True)  # Degrees Celsius
    avg_min_temp = Column(Float, nullable=True)  # Degrees Celsius
    total_precip = Column(Float, nullable=True)  # cm

    __table_args__ = (
        UniqueConstraint('station_id', 'year', name='uix_station_year'),
    )
