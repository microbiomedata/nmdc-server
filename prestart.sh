#!/bin/sh
export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

# TODO: This drops the data base on every start and re-ingests.  At some
#       point we should decide how to do migrations correctly.
# PGDATABASE=postgres psql -c "drop database if exists nmdc;"

echo 'Ingesting data'
# in spin the database already exists
PGDATABASE=postgres psql -c "create database nmdc;" || true

echo 'Upgrading schema and ingesting data'
nmdc-server truncate
nmdc-server migrate  # to create the database if necessary
alembic -c nmdc_server/alembic.ini upgrade head
nmdc-server ingest
