import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models import WeatherRecord, WeatherStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_and_store_stats():
    """
    Calculates weather statistics for each station and year, and stores them in the database.
    """
    session = SessionLocal()
    try:
        # Query to aggregate data
        results = (
            session.query(
                WeatherRecord.station_id,
                func.extract("year", WeatherRecord.date).label("year"),
                func.avg(WeatherRecord.max_temp).label("avg_max_temp"),
                func.avg(WeatherRecord.min_temp).label("avg_min_temp"),
                func.sum(WeatherRecord.precip).label("total_precip"),
            )
            .group_by(WeatherRecord.station_id, "year")
            .all()
        )

        stats_to_upsert = []
        for row in results:
            # Convert total precipitation from mm to cm
            total_precip_cm = (row.total_precip /
                               10.0) if row.total_precip is not None else None

            stats_to_upsert.append({
                "station_id": row.station_id,
                "year": int(row.year),
                "avg_max_temp": row.avg_max_temp,
                "avg_min_temp": row.avg_min_temp,
                "total_precip": total_precip_cm,
            })

        # In a real-world scenario with a more powerful DB, you could use INSERT ... ON CONFLICT
        # For SQLite, we'll delete existing records for the years and stations and then bulk insert.
        for stat in stats_to_upsert:
            session.query(WeatherStats).filter_by(
                station_id=stat["station_id"], year=stat["year"]
            ).delete(synchronize_session=False)

        if stats_to_upsert:
            session.bulk_insert_mappings(WeatherStats, stats_to_upsert)

        session.commit()
        logger.info(
            f"Successfully calculated and stored stats for {len(stats_to_upsert)} records.")

    except Exception as e:
        logger.error(f"Error calculating stats: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    calculate_and_store_stats()
