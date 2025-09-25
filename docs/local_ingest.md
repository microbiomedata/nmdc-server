# Guide to Local Ingest

## What is "local ingest?"

Steps for performing an ingest in a local development environment are documented in [development.md](./development.md). This document describes a process for setting up an ingest that is entirely local to your computer - even the mongo database from which you're ingesting.

## Why do this?

The biggest reason to do this is speed. Some developers experience incredible slowness when ingesting over the `ssh` tunnel as documented elsewhere. Bring the data closer to the destination cuts down on network traffic, and no longer risks being disconnected from NERSC or otherwise running into network issues during ingest.

Another reason in control of the source data. Keeping a copy of the mongo database (even if its a subset of what exists in the cloud) allows you as a developer to change source data and test how it interacts with the ingest process. This way you don't have to touch data in production, and you don't have to worry about the development mongo database being wiped every so often.

If you expect that a change to `nmdc-schema` will affect (break) ingest, you have freedom over your local mongo data to actually test how those changes will interact with ingest.

## Obtaining data for a local mongo database

You'll still need to use an `ssh` tunnel to get an initial set of data (and updated data in the future). Assuming you're using the [sshproxy](https://docs.nersc.gov/connect/mfa/#sshproxy) and have a key, you can establish a tunnel like so:

```bash
ssh -L 0.0.0.0:27018:mongo-loadbalancer.nmdc.production.svc.spin.nersc.org:27017 <nersc_user>@dtn01.nersc.gov -i ~/.ssh/nersc
```

Now your port `27018` will forward to the production mongo database hosted on NERSC.

Here is a simple bash script you can use to back up the data to your local machine. This particular method backs up one collection at a time, and only backs up the collections that ingest needs. You'll need to set some environment variables for this to work.

```bash
host="localhost"
port="27018"
user="org.microbiomedata.data_reader"
password="$SOURCE_MONGO_PASSWORD"
database="nmdc"
authenticationDatabase="admin"
backup_dir="/path/to/mongo/dumps"  # change me

collections=(
    "biosample_set"
    "configuration_set"
    "data_object_set"
    "field_research_site_set"
    "instrument_set"
    "material_sample_set"
    "processed_sample_set"
    "study_set"
    "planned_process_set"
    "collecting_biosamples_from_site_set"
    "data_generation_set"
    "material_processing_set"
    "protocol_execution_set"
    "storage_process_set"
    "workflow_execution_set"
    "manifest_set"
    # The largest collection in mongo. Not necessary for ingest in most cases.
    # If testing gene function annotation ingest/search, you may need this.
    # "functional_annotation_agg"
)

mkdir -p "$backup_dir"

for collection in "${collections[@]}"; do
    echo "backing up collection $collection"
    mongodump --host "$host" --port "$port" --username "$user" --password "$password" --authenticationDatabase "$authenticationDatabase" --db "$database" --collection "$collection" --out "$backup_dir"
done

echo "Backup complete"
```

## Setting up your local mongo database

This part is pretty easy. We can leverage the fact that we're using `docker` in our local development environments to spin up a mongo service with the rest of our stack. If you create a file called `docker-compose.local.yml` and add the following:

```yaml
version: "3.3"
services:
  mongodb_container:
   image: mongo:latest
   environment:
     MONGO_INITDB_ROOT_USERNAME: root
     MONGO_INITDB_ROOT_PASSWORD: rootpassword
   ports:
     - 27017:27017
   container_name: mongo_db
   volumes:
    # For data to persist after this service goes down, we need to mount a volume.
     - /path/to/store/data:/data/db

volumes:
  mongodb_data_container:
```

Then run

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up
```

to spin up the "normal" NMDC server stack with an additional service for mongo.

## Restoring the back up

Here's another very simple script you can run to restore the backup you retrieved earlier into you new local mongo service (the local mongo service must be up for this to work)

```bash
#!/bin/bash

host="localhost"
port="27017"
database="nmdc"
path="/path/to/mongo/dumps"

mongorestore --host "$host" --port "$port" --drop "$path"
```

## Running ingest

First you'll need to make sure your local ingest process knows to pull data from your local mongo. Set the following in your `.env` file:

```
# Settings for ingest from local mongo using docker-compose.local
NMDC_MONGO_HOST="mongo_db"
NMDC_MONGO_PORT=27017
NMDC_MONGO_DATABASE="nmdc"
NMDC_MONGO_USER="root"
NMDC_MONGO_PASSWORD="rootpassword"
```

Then, run ingest via `docker compose`:

```bash
docker compose run --rm backend nmdc-server ingest -vv --skip-annotation
```
