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

# If either database "nmdc_a" or "nmdc_b" doesn't exist yet, create it now so they both exist.
echo "Ensuring databases exist..."
for db_name in "nmdc_a" "nmdc_b"; do
  # Note: This psql command returns "true" if the database exists; otherwise it returns an empty
  #       string. The `--no-psqlrc --tuples-only --no-align` options simplify the result format.
  psql_command="SELECT 'true' FROM pg_database WHERE datname = '${db_name}' LIMIT 1;"
  db_exists=$(PGDATABASE=postgres psql --no-psqlrc --tuples-only --no-align --command "${psql_command}")
  if [ "${db_exists}" = "true" ]; then
    echo "Database exists: ${db_name}"
  else
    echo "Creating database: ${db_name}"
    PGDATABASE=postgres psql --command="CREATE DATABASE ${db_name};"
  fi
done

# Apply pending alembic migrations
nmdc-server migrate

# Generate static content
nmdc-server generate-static-files --remove-existing

# Ensure cloud storage is set up
nmdc-server storage init

## Start the server
uvicorn nmdc_server.asgi:app --host 0.0.0.0 --port 8000
