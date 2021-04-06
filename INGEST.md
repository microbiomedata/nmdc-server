Ingesting source data
=====================

In order to support reingestion of source data with limited down time, the ingestion procedure is
now a two step process.

1. Data is ingested into a staging database `db-ingest`
2. The production database is updated to use data from the staging database.

This currently involves manual intervention to accomplish.  The steps to perform an ingest are as follows:

Ingest into the staging database
--------------------------------

Execute the `POST /api/jobs/ingest` endpoint through the [swagger docs](https://data.microbiomedata.org/docs#/jobs/run_ingest_api_jobs_ingest_post).
This endpoint requires being logged in and having a whitelisted ORCiD.  To add new users to the whitelist, see the code block in
[`auth.py`](https://github.com/microbiomedata/nmdc-server/blob/master/nmdc_server/auth.py#L14-L18).

This job will take several hours to complete.  You should verify it completed successfully by looking at the logs
in [the worker](https://rancher2.spin.nersc.gov/p/c-fwj56:p-nlxq2/workload/deployment:nmdc-dev:worker) before moving
on.


Shut down containers to prevent corrupted data
----------------------------------------------

You will need to shut down the following containers:
* `db-ingest`
* `db`
* `backend`

To do this, first check the services and click "Pause Orchestration".  Next, go into the workload check the running pods and click "Delete".

Note: This will take down the portal until the containers are restarted.

Copy data in the mounted volume
-------------------------------

First shut down the `db-ingest`, `db`, and `backend`  containers to ensure there are no ongoing operations on the databases.
Then, go to `Execute Shell` in the `worker` container.  Inside this shell, run the following:
```
cd /db
timestamp=`date -Isecond -u`
mkdir staging/$timestamp
mv ingest/* staging/$timestamp
ln -sf staging/$timestamp prod
```

You will also likely want to remove old databases at this point to save space in the volume.

Restart the containers
----------------------

Check the services that were shut down before and click "Resume Orchestration".  Everything should come back up within a few seconds.
