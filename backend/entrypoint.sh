#!/bin/hash
set -e

echo "Waiting for database at ${POSTGRES_HOST}:${POSTGRES_PORT}..."
while ! nc -z "${POSTGRES_HOST}" "${POSTGRES_PORT}"; do
  sleep 1
done
echo "Database connected!"

echo "Starting backend server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
