#!/bin/sh
set -e

## Run Alembic migrations
export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

## Wait for the database to be ready
while ! pg_isready ; do
  echo "Waiting for database to be ready..."
  sleep 1;
done

echo 'Creating and migrating database'
# in spin the database already exists
PGDATABASE=postgres psql -c "create database nmdc_a;" || true
PGDATABASE=postgres psql -c "create database nmdc_b;" || true

# Apply pending alembic migrations
nmdc-server migrate

# Generate static content
nmdc-server generate-static-files --remove-existing

# Ensure cloud storage is set up
nmdc-server ensure-storage-buckets

## Start the server
uvicorn nmdc_server.asgi:app --host 0.0.0.0 --port 8000
