Ingesting source data
=====================

In order to support reingestion of source data with limited down time, the ingestion procedure is
now a two step process.

1. Data is ingested into a staging database
2. The staging and production database are swapped in spin

This currently involves manual intervention to accomplish.  The steps to perform an ingest are as follows:

Ingest into the staging database
--------------------------------

Execute the `POST /api/jobs/ingest` endpoint through the [swagger docs](https://data.microbiomedata.org/docs#/jobs/run_ingest_api_jobs_ingest_post).
This endpoint requires being logged in and having a whitelisted ORCiD.  To add new users to the whitelist, see the code block in
[`auth.py`](https://github.com/microbiomedata/nmdc-server/blob/main/nmdc_server/auth.py#L14-L18).

This job will take several hours to complete.  You should verify it completed successfully by looking at the logs
in [the worker](https://rancher2.spin.nersc.gov/p/c-fwj56:p-nlxq2/workload/deployment:nmdc-dev:worker) before moving
on.


Modify environment variables to swap prod/staging
-------------------------------------------------

In the rancher2 UI, select `Resources->Secrets` from the toolbar and click on the `postgres` secret group.  Now, click on the
button in the upper right with three vertical dots and select `Edit`.  Now, swap the values under `INGEST_URI` and `POSTGRES_URI`
and click save.

Restart the containers
----------------------

Go back to the workloads page and redeploy both the `backend` and `worker`
services.  If the site doesn't work with the newest data, you can always revert
the changes to the secrets provided you haven't started a new ingest.
