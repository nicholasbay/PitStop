#!/bin/hash
set -e

echo "Fetch parking spots data..."
python scripts/fetch_parking_spots.py

echo "Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; do
  sleep 1
done
echo "Database connected!"

echo "Loading parking spots into database..."
python scripts/load_parking_spots.py

echo "Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
