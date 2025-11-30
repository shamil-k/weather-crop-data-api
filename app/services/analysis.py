import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models import WeatherRecord, WeatherStats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_and_store_stats():
    """
    Calculates yearly weather statistics and upserts them into the `weather_stats` table.

    This function aggregates the raw weather data to compute yearly averages for
    temperatures and total precipitation. It's designed to be run periodically
    (e.g., after new data ingestion) to keep the statistical summary up-to-date.
    The use of a separate stats table (materialized view pattern) is a key
    performance optimization for the API.
    """
    session = SessionLocal()
    try:
        # This single query efficiently calculates all required statistics at the database level.
        # Using `func.avg` and `func.sum` offloads the heavy computation to the database engine,
        # which is much faster than pulling raw data into Python and calculating manually.
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
            # Perform unit conversion for precipitation from mm to cm as required.
            total_precip_cm = (row.total_precip /
                               10.0) if row.total_precip is not None else None

            stats_to_upsert.append({
                "station_id": row.station_id,
                "year": int(row.year),
                "avg_max_temp": row.avg_max_temp,
                "avg_min_temp": row.avg_min_temp,
                "total_precip": total_precip_cm,
            })

        # For idempotency, we perform an "upsert" operation.
        # Since SQLite has limited support for `INSERT ... ON CONFLICT`, the chosen strategy
        # is to delete any existing records for the station-year pairs and then bulk insert
        # the newly calculated stats. This is a simple and effective approach for this context.
        # For databases like PostgreSQL, a more direct `ON CONFLICT DO UPDATE` would be preferable.
        if stats_to_upsert:
            # Extract station-year pairs to delete existing records.
            station_year_pairs = [(s['station_id'], s['year'])
                                  for s in stats_to_upsert]

            # Delete all existing stats records that are about to be replaced.
            # This is done in a single delete operation for efficiency.
            for station_id, year in station_year_pairs:
                session.query(WeatherStats).filter_by(
                    station_id=station_id, year=year
                ).delete(synchronize_session=False)

            # Bulk insert the new statistics.
            session.bulk_insert_mappings(WeatherStats, stats_to_upsert)

        session.commit()
        logger.info(
            f"Successfully calculated and stored stats for {len(stats_to_upsert)} records.")

    except Exception as e:
        logger.error(f"An error occurred during statistics calculation: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    calculate_and_store_stats()
