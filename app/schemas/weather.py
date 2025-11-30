from datetime import date
from pydantic import BaseModel


class WeatherRecordBase(BaseModel):
    station_id: str
    date: date
    max_temp: float | None
    min_temp: float | None
    precip: float | None


class WeatherRecordCreate(WeatherRecordBase):
    pass


class WeatherRecord(WeatherRecordBase):
    id: int

    class Config:
        orm_mode = True


class WeatherStatsBase(BaseModel):
    station_id: str
    year: int
    avg_max_temp: float | None
    avg_min_temp: float | None
    total_precip: float | None


class WeatherStats(WeatherStatsBase):
    id: int

    class Config:
        orm_mode = True
