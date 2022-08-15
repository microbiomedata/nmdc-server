#!/bin/sh
set -e

export PGUSER PGPASSWORD PGDATABASE PGHOST POSTGRES_URI

while ! PGDATABASE=postgres psql --quiet -c "select * from user" ; do
    sleep 1;
done

echo 'Creating and migrating database'
# in spin the database already exists
PGDATABASE=postgres psql -c "create database nmdc_a;" \
|| pg_dump \
    --table "user_logins" \
    --table "submission_metadata" \
    --table "file_download" \
    --file "nmdc_a-$(date +%s)-$(openssl rand -hex 32).sql" \
    --data-only \
    nmdc_a


PGDATABASE=postgres psql -c "create database nmdc_b;" \
|| pg_dump \
    --table "user_logins" \
    --table "submission_metadata" \
    --table "file_download" \
    --file "nmdc_b-$(date +%s)-$(openssl rand -hex 32).sql" \
    --data-only \
    nmdc_b

nmdc-server migrate
