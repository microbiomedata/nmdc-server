#!/bin/sh
source /app/.env
export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

# TODO: This drops the data base on every start and re-ingests.  At some
#       point we should decide how to do migrations correctly.
PGDATABASE=postgres psql -c "drop database if exists nmdc;"

echo 'Ingesting data'
PGDATABASE=postgres psql -c "create database nmdc;"
python /app/create_database.py

echo 'Upgrading schema'
alembic upgrade head
