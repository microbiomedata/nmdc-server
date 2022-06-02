# NMDC Server and Client Portal

## Requirements

* install docker and docker-compose
* install submodules via `git submodule update --init --recursive`

## Development Setup (with docker)

### Configuration

```bash
cp .env.example .env
```

Edit values in `.env` to point to existing postgresql databases.

### OAuth setup

See `nmdc_server/config` for configuration.  Env variable names begin with `NMDC_`.

1. Create an OrcID account at orcid.org
1. Create an OrcID API Token in the [developer tools](https://orcid.org/developer-tools)
1. Set the redirect URIs to `http://localhost:8080`
1. Set the following configuration in `.env`, and then restart the stack.

```bash
NMDC_CLIENT_ID=changeme
NMDC_CLIENT_SECRET=changeme
NMDC_HOST=http://localhost:8080
```

### Running the server

```bash
docker-compose up
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/docs`.

**NOTE**: If you have migration issues when starting up the server, you can purge the volume and start
from scratch by running the following, then re-running ingestion (above).

```bash
docker-compose down
docker volume rm -f nmdc-server_app-db-data
```

## Development Setup (outside docker)

```bash
# Run the service dependencies (db, queue)
docker-compose up -d
```

With python virtualenv. Requires Python 3.7+

```bash
pip install -e .
pip install uvicorn tox

uvicorn nmdc_server.asgi:app --reload
```

View swagger page at `http://localhost:8000/docs`.

## Running ingest

You need an active SSH tunnel connection to nersc attached to the compose network.  After running docker-compose up, run this container.

If you haven't already, [set up MFA on your NERSC account](https://docs.nersc.gov/connect/mfa/) (it's required for SSHing in).

```bash
export NERSC_USER=changeme
docker run --rm -it -p 27017:27017 --network nmdc-server_default --name tunnel kroniak/ssh-client ssh -o StrictHostKeyChecking=no -L 0.0.0.0:27017:mongo-loadbalancer.nmdc-runtime-dev.development.svc.spin.nersc.org:27017 $NERSC_USER@dtn01.nersc.gov '/bin/bash -c "while [[ 1 ]]; do echo heartbeat; sleep 300; done"'
```

You can connect to the instance manually

```bash
docker run -d -p 3000:3000 --network nmdc-server_default mongoclient/mongoclient
```

In order to populate the database, you must create a `.env` file in the top
level directory containing mongo credentials.

```bash
# .env
NMDC_MONGO_USER=changeme
NMDC_MONGO_PASSWORD=changeme
```

With that file in place, populate the docker volume by running,

```bash
docker-compose run backend nmdc-server truncate # if necessary
docker-compose run backend nmdc-server migrate
docker-compose run backend nmdc-server ingest
```

## Submission portal development

This is a temporary solution while the separation of concerns is established.

``` bash
# Clone DataHarmonizer https://github.com/microbiomedata/DataHarmonizer
# cd into the DataHarmonizer Directory
npx http-server -p 3333 .

# In another terminal
cd web/
yarn
yarn serve
```

You should now be able to load the submission portal as http://localhost:8080/submission/samples

In production, the DataHarmonizer iframe will be served from GitHub Pages.

## Testing

```bash
tox
```

## Troubleshooting

Occasionally, a migration will fail to run correctly.  This will cause data ingestion to fail.
The fix is to drop the existing database and to restart the service.  In docker-compose, this
can be done by running

```bash
docker-compose run backend psql postgres -c 'drop database nmdc_a;'
```

On Spin, you can use the web interface to start a shell on the `db` instance and run:

```bash
psql -U postgres postgres -c 'drop database nmdc_a;'
```

Then, redeploy the backend service.

## Generating new migrations

The way this project [injects](nmdc_server/migrations/env.py) the database uri
into alembic's configuration does not work when using alembic's CLI.  To
generate a new migration, you must modify `nmdc_server/alembic.ini` and hard
code your database uri to `sqlalchemy.url`.  After doing that, you can run alembic
commands as usual, e.g.

```bash
alembic -c nmdc_server/alembic.ini revision --autogenerate
```

## Developing with the shell

A handy IPython shell is provided with some commonly used symbols automatically
imported, and `autoreload 2` enabled. To run it:

```bash
docker-compose run --rm backend nmdc-server shell
```

You can also pass `--print-sql` to output all SQL queries.
