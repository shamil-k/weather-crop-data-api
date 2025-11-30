import os
import glob
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models import WeatherRecord, Base

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def process_file(file_path: str) -> list[dict]:
    """
    Parses a single weather data file and returns a list of record dictionaries.

    This function is designed to be run in parallel.It handles reading the file,
    parsing lines, converting data types, and handling missing values (-9999).
    It does NOT interact with the database to avoid locking issues.
    """
    station_id = os.path.basename(file_path).replace(".txt", "")
    records_to_insert = []
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) != 4:
                continue

            date_str, max_temp_str, min_temp_str, precip_str = parts
            try:
                record_date = datetime.strptime(date_str, "%Y%m%d").date()
            except ValueError:
                continue

            def process_value(val_str):
                val = int(val_str)
                return None if val == -9999 else val

            max_temp_tenths = process_value(max_temp_str)
            min_temp_tenths = process_value(min_temp_str)
            precip_tenths = process_value(precip_str)
            max_temp = max_temp_tenths / \
                10.0 if max_temp_tenths is not None else None
            min_temp = min_temp_tenths / \
                10.0 if min_temp_tenths is not None else None
            precip = precip_tenths / 10.0 if precip_tenths is not None else None

            records_to_insert.append({
                'station_id': station_id,
                'date': record_date,
                'max_temp': max_temp,
                'min_temp': min_temp,
                'precip': precip
            })
    return records_to_insert


def ingest_data(data_dir: str):
    """
    Orchestrates the ingestion of weather data.

    Steps:
    1.  **Parallel Processing**: Uses a ProcessPoolExecutor to parse text files concurrently.
        This significantly speeds up reading and data conversion.
    2.  **Aggregation**: Collects all parsed records from the worker processes.
    3.  **Database Insertion**: Performs a bulk insert of new records into the database.
        Checks for existing records to maintain idempotency and avoids duplicates.
    """
    start_time = datetime.now()
    logger.info(f"Ingestion started at {start_time}")

    Base.metadata.create_all(bind=engine)

    files = glob.glob(os.path.join(data_dir, "*.txt"))
    all_records = []

    # Check for sequential mode (useful for Cloud Run/Serverless where /dev/shm is limited)
    if os.environ.get('SEQUENTIAL_INGEST', 'false').lower() == 'true':
        logger.info("Running in sequential mode (SEQUENTIAL_INGEST=true)")
        for i, file_path in enumerate(files):
            all_records.extend(process_file(file_path))
            logger.info(f"Processed file {i + 1}/{len(files)}")
    else:
        # Calculate an optimal chunk size for the process pool
        chunksize = max(1, len(files) // (multiprocessing.cpu_count() * 2))

        # Use 'spawn' context for better compatibility across OS (especially Windows)
        with ProcessPoolExecutor(mp_context=multiprocessing.get_context('spawn')) as executor:
            results = executor.map(process_file, files, chunksize=chunksize)
            for i, result in enumerate(results):
                all_records.extend(result)
                logger.info(f"Processed file {i + 1}/{len(files)}")

    session = SessionLocal()
    total_new_records = 0
    try:
        logger.info("Starting database insertion...")
        station_ids = sorted(list({rec['station_id'] for rec in all_records}))
        total_stations = len(station_ids)

        for i, station_id in enumerate(station_ids):
            existing_dates = session.query(WeatherRecord.date).filter(
                WeatherRecord.station_id == station_id).all()
            existing_dates_set = {d[0] for d in existing_dates}

            records_for_station = [
                rec for rec in all_records if rec['station_id'] == station_id]

            # Use dictionaries directly for bulk_insert_mappings
            new_records_dicts = [
                rec for rec in records_for_station if rec['date'] not in existing_dates_set
            ]

            if new_records_dicts:
                session.bulk_insert_mappings(WeatherRecord, new_records_dicts)
                total_new_records += len(new_records_dicts)

            if (i + 1) % 10 == 0 or (i + 1) == total_stations:
                logger.info(
                    f"Processed station {i + 1}/{total_stations}")

        session.commit()
    except Exception as e:
        logger.error(f"Error during bulk insert: {e}")
        session.rollback()
    finally:
        session.close()

    end_time = datetime.now()
    logger.info(f"Ingestion finished at {end_time}")
    logger.info(f"Total new records ingested: {total_new_records}")
    logger.info(f"Total time taken: {end_time - start_time}")


if __name__ == "__main__":
    ingest_data("app/artifacts/wx_data")
