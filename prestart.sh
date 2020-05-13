#!/bin/sh
source /app/.env
export PGUSER PGPASSWORD PGDATABASE POSTGRES_URI

while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

if ! psql ${POSTGRES_URI} &> /dev/null ; then
    echo 'Ingesting data'
    PGDATABASE=postgres psql -c "create database nmdc;"
    python /app/create_database.py
fi

echo 'Upgrading schema'
alembic upgrade head
