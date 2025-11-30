import os
import glob
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import WeatherRecord, Base

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def ingest_data(data_dir: str):
    """
    Ingests weather data from text files into the database.

    This function is designed to be idempotent; running it multiple times will not
    create duplicate records. It processes files in a given directory, performs
    data validation and unit conversions, and uses a bulk-insert strategy for
    efficiency.

    Args:
        data_dir: The path to the directory containing the weather data files.
    """
    start_time = datetime.now()
    logger.info(f"Ingestion started at {start_time}")

    # Ensures tables are created before ingestion. Safe to run multiple times.
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    total_records = 0

    try:
        files = glob.glob(os.path.join(data_dir, "*.txt"))
        for file_path in files:
            station_id = os.path.basename(file_path).replace(".txt", "")
            logger.info(f"Processing file for station: {station_id}")

            with open(file_path, 'r') as f:
                records_to_insert = []
                for line in f:
                    parts = line.strip().split('\t')
                    # Basic validation: ensure the line has the correct number of columns.
                    if len(parts) != 4:
                        continue

                    date_str, max_temp_str, min_temp_str, precip_str = parts

                    # Data cleaning and type conversion.
                    try:
                        record_date = datetime.strptime(
                            date_str, "%Y%m%d").date()
                    except ValueError:
                        # Skip malformed dates.
                        continue

                    # A helper function to handle the -9999 missing value indicator.
                    def process_value(val_str):
                        val = int(val_str)
                        return None if val == -9999 else val

                    max_temp_tenths = process_value(max_temp_str)
                    min_temp_tenths = process_value(min_temp_str)
                    precip_tenths = process_value(precip_str)

                    # Unit conversion as per the problem specification.
                    # Temperature: from tenths of a degree C to degrees C.
                    # Precipitation: from tenths of a mm to mm.
                    max_temp = max_temp_tenths / 10.0 if max_temp_tenths is not None else None
                    min_temp = min_temp_tenths / 10.0 if min_temp_tenths is not None else None
                    precip = precip_tenths / 10.0 if precip_tenths is not None else None

                    # Staging records in a list for bulk processing.
                    records_to_insert.append({
                        'station_id': station_id,
                        'date': record_date,
                        'max_temp': max_temp,
                        'min_temp': min_temp,
                        'precip': precip
                    })

                # After reading a whole file, process the records for insertion.
                if records_to_insert:
                    # To ensure idempotency, fetch all existing dates for the current station.
                    # This check is performed in memory in the Python client, which is
                    # significantly more performant than handling potential unique constraint
                    # violations from the database for every single row.
                    existing_dates = session.query(WeatherRecord.date).filter(
                        WeatherRecord.station_id == station_id
                    ).all()
                    existing_dates_set = {d[0] for d in existing_dates}

                    # Filter out records that already exist in the database.
                    new_records = [
                        WeatherRecord(**rec)
                        for rec in records_to_insert
                        if rec['date'] not in existing_dates_set
                    ]

                    # Perform a bulk save operation, which is much faster than individual inserts.
                    if new_records:
                        session.bulk_save_objects(new_records)
                        session.commit()
                        total_records += len(new_records)
                        logger.info(
                            f"Inserted {len(new_records)} new records for {station_id}")
                    else:
                        logger.info(
                            f"No new records to insert for {station_id}")

    except Exception as e:
        logger.error(f"A critical error occurred during ingestion: {e}")
        session.rollback()
    finally:
        # It's crucial to close the session to release database connections.
        session.close()

    end_time = datetime.now()
    logger.info(f"Ingestion finished at {end_time}")
    logger.info(f"Total new records ingested: {total_records}")
    logger.info(f"Total time taken: {end_time - start_time}")


if __name__ == "__main__":
    ingest_data("app/artifacts/wx_data")
