# Guide to Local Ingest

## What is "local ingest?"

Steps for performing an ingest in a local development environment are documented in [development.md](./development.md). This document describes a process for setting up an ingest that is entirely local to your computer - even the mongo database from which you're ingesting.

## Why do this?

The biggest reason to do this is speed. Some developers experience incredible slowness when ingesting over the `ssh` tunnel as documented elsewhere. Bringing the data closer to the destination cuts down on network traffic, and no longer risks being disconnected from NERSC or otherwise running into network issues during ingest.

Another reason is control of the source data. Keeping a copy of the mongo database (even if its a subset of what exists in the cloud) allows you as a developer to change source data and test how it interacts with the ingest process. This way you don't have to touch data in production, and you don't have to worry about the development mongo database being wiped every so often.

If you expect that a change to `nmdc-schema` will affect (break) ingest, you have freedom over your local mongo data to actually test how those changes will interact with ingest.

## Step 1: Dump data from MongoDB

You'll need an SSH tunnel to the MongoDB instance you want to dump from. Once the tunnel is active, use the `scripts/mongo_dump.sh` script to dump the ingest-relevant collections to `data/mongo/` (which is gitignored).

```bash
# Dump from dev MongoDB (tunnel on port 37018):
./scripts/mongo_dump.sh <user> <password> 37018

# Dump from prod MongoDB (tunnel on port 27124, the default):
./scripts/mongo_dump.sh <user> <password>
```

See `scripts/mongo_dump.sh` for the full list of arguments and options, including how to include the `functional_annotation_agg` collection (needed only for gene function annotation testing).

## Step 2: Start a local MongoDB container

Create a `docker-compose.local.yml` file at the root of this repository with the following contents:

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
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

The named volume (`mongodb_data`) ensures data persists across container restarts — you only need to restore the dump once.

Start just the MongoDB container:

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d mongodb_container
```

## Step 3: Restore the dump

Use the `scripts/mongo_restore.sh` script to restore the dump into the local container:

```bash
./scripts/mongo_restore.sh
```

The tunnel is no longer needed after this point.

## Step 4: Obtain static files used by the ingester

The ingester requires some static files to be present at `/data/ingest` within the container
it's running in.

For our purposes, the authoritative copies of those static files reside within the following
`ingest` directory on the NERSC filesystem:

```shell
/global/cfs/cdirs/m3408/ingest
```

Download that `ingest` directory and its contents, and save it into the `./data` directory
in the root directory of this repository; so that you end up with the following file tree:

```shell
# Run this command from the root directory of this repository.
$ ls ./data/ingest/* 
./data/ingest/cog:
cog-20.def.tab  fun-20.tab

./data/ingest/go:
ko2go.tsv               pfam_go_mappings.txt

./data/ingest/kegg:
kegg_pathway.tab.txt

./data/ingest/pfam:
Pfam-A.clans.tsv
```

Since the `docker-compose.yml` file mounts the host's `./data/ingest` directory at `/data/ingest`
within the `backend` container, these files will be present where the ingester expects them.

## Step 5: Configure `.env` for the local MongoDB

Set the following in your `.env` file so the ingest process connects to the local container
instead of the remote tunnel:

```
# Settings for ingest from local mongo using docker-compose.local.yml
NMDC_MONGO_HOST="mongo_db"
NMDC_MONGO_PORT=27017
NMDC_MONGO_DATABASE="nmdc"
NMDC_MONGO_USER="root"
NMDC_MONGO_PASSWORD="rootpassword"
```

## Step 6: Run ingest

```bash
docker compose run --rm backend nmdc-server ingest -vv --skip-annotation
```

> **Note**: `--skip-annotation` omits metagenome/metatranscriptome annotation loading, which is
> the slowest part of ingest (several hours). Omit this flag only if you specifically need to test
> gene function annotation. You can also use `--function-limit N` to cap the number of gene
> functions loaded per workflow (e.g. `--function-limit 10`) for a faster partial run.
