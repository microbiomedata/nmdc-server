#!/bin/sh
set -e

export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

echo 'Creating and migrating database'
# in spin the database already exists
PGDATABASE=postgres psql -c "create database nmdc;" || true


nmdc-server migrate
