# NMDC Data Portal

The data portal is **not** a system of record for NMDC Data. It is a transformed copy of the system of record from MongoDB, transformed into a relational schema optimized for the sort of queries that the data portal client needs to make.

The NMDC Data Portal is build with these technologies

* Python and [FastAPI](https://fastapi.tiangolo.com/)
* PostgreSQL and SQLAlchemy
* Celery and Redis Queue
* Vue JS and Vuetify

### Software versions

* [Python version dependencies](https://github.com/microbiomedata/nmdc-server/blob/main/setup.py)
* [Javascript version dependencies](https://github.com/microbiomedata/nmdc-server/blob/main/web/package.json)

## General architecture

![nmdc-diagram](nmdc-diagram.svg)

## API Documentation

Information about how to use the search portal REST API can be found in the [wiki](https://github.com/microbiomedata/nmdc-server/wiki/Search-API-Docs).

## Development documentation

* [Server and client development documentation](https://github.com/microbiomedata/nmdc-server)
* [Client architecture notes](https://github.com/microbiomedata/nmdc-server/blob/main/web/README.md)

## Data Ingest

The ingestion procedure is a two step process.

1. Data is ingested into a staging database
2. The staging and production database are swapped in spin

The steps to perform an ingest are as follows:

### Step 1. Ingest into the staging database

Execute the `POST /api/jobs/ingest` endpoint through the [swagger docs](https://data.microbiomedata.org/docs#/jobs/run_ingest_api_jobs_ingest_post).

This endpoint requires being logged in and having a whitelisted ORCiD.  To add new users to the whitelist, see the code block in [`auth.py`](hhttps://github.com/microbiomedata/nmdc-server/blob/main/nmdc_server/auth.py).

This job will take several hours to complete.  You should verify it completed successfully by looking at the logs in [the worker](https://rancher2.spin.nersc.gov/p/c-fwj56:p-nlxq2/workload/deployment:nmdc-dev:worker) before moving on.

### Step 2. Modify environment variables to swap prod/staging

In the rancher2 UI, select `Resources->Secrets` from the toolbar and click on the `postgres` secret group.  Now, click on the button in the upper right with three vertical dots and select `Edit`.  Now, swap the values under `INGEST_URI` and `POSTGRES_URI` and click save.

### Step 3. Restart the containers

Go back to the workloads page and redeploy both the `backend` and `worker` services.  If the site doesn't work with the newest data, you can always revert the changes to the secrets provided you haven't started a new ingest.
