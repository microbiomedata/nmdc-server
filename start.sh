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
#
# Explanations of the commands used in this block:
# - `$ psql --list --tuples-only` dumps a table whose first column contains database names
#   and whose column borders are drawn using '|' characters (like a Markdown table).
# - `$ cut -d '|' -f 1` captures the database names, which are in the first column of that table.
# - `$ grep --quiet --word-regexp "${db_name}"` returns a success status if this name is among them.
#   A success status will cause the `&&` to execute, resulting in `db_exists` containing "true".
#
echo 'Ensuring databases exist'
for db_name in "nmdc_a" "nmdc_b"; do
  db_names=$(PGDATABASE=postgres psql --list --tuples-only | cut -d '|' -f 1)
  db_exists=$(echo "${db_names}" | grep --quiet --word-regexp "${db_name}" && echo "true" || echo "false")
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
