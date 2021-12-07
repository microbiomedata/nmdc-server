# NMDC Server and Client Portal

## Getting started with Docker

* install [ldc](https://github.com/Kitware/ldc)
* install submodules via `git submodule update --init --recursive`

In order to populate the database, you must create a `.env` file in the top
level directory containing mongo credentials.

```bash
# .env
NMDC_MONGO_USER=changeme
NMDC_MONGO_PASSWORD=changeme
```

With that file in place, populate the docker volume by running,

```bash
ldc run backend nmdc-server truncate # if necessary
ldc run backend nmdc-server migrate
ldc run backend nmdc-server ingest
```

Then you can start up the services.

```bash
ldc up
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/docs`.

**NOTE**: If you have migration issues when starting up the server, you can purge the volume and start
from scratch by running the following, then re-running ingestion (above).

```bash
ldc down
docker volume rm -f nmdc-server_app-db-data
```

### Development Installation

### Configuration

```bash
cp .env.example .env
```

Edit values in `.env` to point to existing postgresql databases.

#### OAuth setup

See `nmdc_server/config` for configuration.  Env variable names begin with `NMDC_`.

At minimum, after creating a new OrcID API, you'll need to set these.

```bash
NMDC_CLIENT_ID=changeme
NMDC_CLIENT_SECRET=changeme
NMDC_HOST=http://localhost:8080
```

### Run (development)

With docker and LDC

```bash
ldc dev up -d
```

With python virtualenv. Requires Python 3.7+

```bash
pip install -e .
pip install uvicorn tox

uvicorn nmdc_server.asgi:app --reload
```

View swagger page at `http://localhost:8000/docs`.

### Testing

```bash
tox
```

### Troubleshooting

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

### Generating new migrations

The way this project [injects](nmdc_server/migrations/env.py) the database uri
into alembic's configuration does not work when using alembic's CLI.  To
generate a new migration, you must modify `nmdc_server/alembic.ini` and hard
code your database uri to `sqlalchemy.url`.  After doing that, you can run alembic
commands as usual, e.g.

```bash
alembic -c nmdc_server/alembic.ini revision --autogenerate
```

### Developing with the shell

A handy IPython shell is provided with some commonly used symbols automatically
imported, and `autoreload 2` enabled. To run it:

```bash
ldc dev run --rm backend nmdc-server shell
```

You can also pass `--print-sql` to output all SQL queries.
