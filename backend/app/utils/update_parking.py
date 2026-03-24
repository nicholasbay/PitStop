from datetime import datetime
import json
import logging
from pathlib import Path
from typing import List

import psycopg
import requests

from app.config import get_settings
from app.db import get_db_connection

ROOT_PATH = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_PATH / 'data'
DATA_PATH.mkdir(exist_ok=True)

DATAMALL_URL = 'https://datamall2.mytransport.sg/ltaodataservice/BicycleParkingv2'
DISTANCE_KM = 5
TIMEOUT_S = 20
LOCATIONS_FILE = DATA_PATH / 'locations.json'
NDJSON_FILE = DATA_PATH / f'spots_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.ndjson'
BATCH_SIZE = 1000

logger = logging.getLogger(__name__)
settings = get_settings()

def fetch_and_update_spots(snapshot: bool = False) -> None:
    all_spots = []

    try:
        # Fetch
        locations = _load_locations(LOCATIONS_FILE)
        for loc in locations:
            lat = loc.get('Latitude')
            lon = loc.get('Longitude')

            if not lat or not lon:
                logger.warning(f"Skipping location with missing coordinates: {loc}")
                continue

            spots = _fetch_spots(lat, lon)
            all_spots.extend(spots)

        logger.info(f"Fetched {len(all_spots)} from {len(locations)} locations")

        # Save snapshot of fetched data
        if snapshot:
            _save_snapshot(all_spots)

        # Update
        transformed_spots = _transform_spots(all_spots)
        with get_db_connection() as conn:
            for i in range(0, len(transformed_spots), BATCH_SIZE):
                batch = transformed_spots[i:i + BATCH_SIZE]
                _upsert_batch(conn, batch)

        logger.info(f"Upserted {len(transformed_spots)} spots")
    except Exception as e:
        logger.error(e)


def _load_locations(path: Path) -> List:
    """Load location data from locations.json file."""
    try:
        with open(path, 'r') as f:
            locations = json.load(f)
        logger.debug(f"Loaded {len(locations)} locations from {path}")
        return locations
    except FileNotFoundError:
        logger.error(f"File not found: {path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        raise


def _fetch_spots(lat: float, lon: float) -> List:
    # Fetch parking spots from DATAMALL API for a specified location
    params = {
        'Lat': lat,
        'Long': lon,
        'Dist': DISTANCE_KM
    }
    headers = {'AccountKey': settings.DATAMALL_ACCOUNT_KEY}

    try:
        response = requests.get(DATAMALL_URL, params=params, headers=headers, timeout=TIMEOUT_S)
        response.raise_for_status()

        data = response.json()
        parking_spots = data.get('value', [])
        logger.debug(f"Fetched {len(parking_spots)} parking spots for location ({lat}, {lon})")
        return parking_spots
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for location ({lat}, {lon}): {e}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response for location ({lat}, {lon}): {e}")
        return []


def _save_snapshot(spots: List) -> None:
    """Save fetched parking spots to an NDJSON file."""
    path = DATA_PATH / f'spots_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.ndjson'
    try:
        with open(path, 'w') as f:
            for spot in spots:
                f.write(json.dumps(spot) + '\n')

            logger.debug(f"Saved {len(spots)} spots to {path}")
    except IOError as e:
        logger.error(f"Error occurred while saving snapshot: {e}")


def _transform_spots(spots: List) -> List:
    """
    Transform parking spots returned by API into database format.
    """
    transformed = []
    for spot in spots:
        # Map NDJSON fields to database columns
        # Note: PostgreSQL POINT uses (longitude, latitude) order
        data = (
            spot.get('Description'),
            spot.get('Longitude'),  # longitude first for POINT
            spot.get('Latitude'),   # latitude second for POINT
            spot.get('RackType'),
            spot.get('RackCount'),
            spot.get('ShelterIndicator')
        )
        transformed.append(data)
    return transformed


def _upsert_batch(conn: psycopg.connection, batch: List) -> None:
    """
    Upsert transformed parking spots into the database.
    """
    upsert_query = """
        INSERT INTO parking_spots (description, coordinates, rack_type, rack_count, shelter_indicator)
        VALUES (%s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s)
        ON CONFLICT (description)
        DO UPDATE SET
            coordinates = EXCLUDED.coordinates,
            rack_type = EXCLUDED.rack_type,
            rack_count = EXCLUDED.rack_count,
            shelter_indicator = EXCLUDED.shelter_indicator;
    """

    with conn.cursor() as cursor:
        try:
            cursor.executemany(upsert_query, batch)
            conn.commit()
        except psycopg.Error as e:
            logger.error(f"Database error during batch upsert: {e}")
            conn.rollback()
