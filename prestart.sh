#!/bin/sh
set -e

# This script is run before the server application starts by the tiangolo/uvicorn-gunicorn
# image. See: https://github.com/tiangolo/uvicorn-gunicorn-docker#custom-appprestartsh

export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

# Wait for the database to be ready
while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

# Apply pending alembic migrations
nmdc-server migrate
