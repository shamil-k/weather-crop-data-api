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
    start_time = datetime.now()
    logger.info(f"Ingestion started at {start_time}")

    # Create tables if they don't exist
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
                    if len(parts) != 4:
                        continue

                    date_str, max_temp_str, min_temp_str, precip_str = parts

                    # Date formatting
                    try:
                        record_date = datetime.strptime(
                            date_str, "%Y%m%d").date()
                    except ValueError:
                        continue

                    # Helper to process values
                    def process_value(val_str):
                        val = int(val_str)
                        if val == -9999:
                            return None
                        return val

                    max_temp_tenths = process_value(max_temp_str)
                    min_temp_tenths = process_value(min_temp_str)
                    precip_tenths = process_value(precip_str)

                    # Unit conversion
                    # Temperature: tenths of degree C -> degrees C
                    # Precipitation: tenths of mm -> mm
                    max_temp = max_temp_tenths / 10.0 if max_temp_tenths is not None else None
                    min_temp = min_temp_tenths / 10.0 if min_temp_tenths is not None else None
                    precip = precip_tenths / 10.0 if precip_tenths is not None else None

                    # Collect all records first

                    records_to_insert.append({
                        'station_id': station_id,
                        'date': record_date,
                        'max_temp': max_temp,
                        'min_temp': min_temp,
                        'precip': precip
                    })

                # Bulk insert logic
                if records_to_insert:
                    # Get existing dates for this station to filter duplicates in Python
                    # This is faster than checking one by one in DB or handling DB errors for bulk
                    existing_dates = session.query(WeatherRecord.date).filter(
                        WeatherRecord.station_id == station_id
                    ).all()
                    existing_dates_set = {d[0] for d in existing_dates}

                    new_records = [
                        WeatherRecord(**rec)
                        for rec in records_to_insert
                        if rec['date'] not in existing_dates_set
                    ]

                    if new_records:
                        session.bulk_save_objects(new_records)
                        session.commit()
                        total_records += len(new_records)
                        logger.info(
                            f"Inserted {len(new_records)} records for {station_id}")
                    else:
                        logger.info(f"No new records for {station_id}")

    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        session.rollback()
    finally:
        session.close()

    end_time = datetime.now()
    logger.info(f"Ingestion finished at {end_time}")
    logger.info(f"Total records ingested: {total_records}")
    logger.info(f"Time taken: {end_time - start_time}")


if __name__ == "__main__":
    ingest_data("artifacts/wx_data")
