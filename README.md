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
1. Set the redirect URIs to `http://localhost:8080` (Ignore the error about https, it's just a warning).
1. Set the following configuration in `.env`, and then restart the stack.

```bash
NMDC_CLIENT_ID=changeme
NMDC_CLIENT_SECRET=changeme
NMDC_HOST=http://localhost:8080
```

### Running the server

```bash
docker-compose up -d
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/docs`.

## Development Setup (outside docker)

```bash
# Start only the service dependencies.
docker-compose up -d db data redis
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
docker-compose run backend nmdc-server -vv ingest --function-limit 100
```

## Running the client

Run the client in development mode.

``` bash
cd web/
yarn
yarn serve
```

**Note**: To authenticate, log into the portal at `http://localhost:8080` first.  Then, the dev environment portal at `http://localhost:8081` will also be authenticated.  This is because oauth with webpack dev server is not possible.

## Testing

```bash
tox
```

## Generating new migrations

```bash
# Autogenerate a migration diff from the current HEAD
docker-compose run backend alembic -c nmdc_server/alembic.ini revision --autogenerate
```

In order to generate a migration, your database state should match HEAD.  If you started the server from a totally empty database, then the default behavior is to ignore migration scripts and set up the database to match `models.py`.  Before you can generate a migration, you need to reset your database to match HEAD.

```bash
# Destroy everything.  You'll lose your data!
docker-compose down -v
docker-compose up -d db
# Create the database
docker-compose run backend psql -c "create database nmdc_a;" -d postgres
# Run migrations to HEAD
docker-compose run backend alembic -c nmdc_server/alembic.ini upgrade head
# Autogenerate a migration diff from the current HEAD
docker-compose run backend alembic -c nmdc_server/alembic.ini revision --autogenerate
```

## Postgres import and export

```bash
# export, and 
docker-compose run backend bash -c 'pg_dump nmdc_a > /app/nmdc_server/nmdc_a.sql'

# import -- starting from an EMPTY database with DB running
docker-compose down -v
docker-compose up -d db
docker-compose run backend psql -c "create database nmdc_a;" -d postgres
cp downloads/nmdc_a.sql nmdc_server/nmdc_a.sql
docker-compose run backend bash -c 'psql nmdc_a < /app/nmdc_server/nmdc_a.sql'
docker-compose run backend nmdc-server migrate # stamp the migration db
```

## Developing with the shell

A handy IPython shell is provided with some commonly used symbols automatically
imported, and `autoreload 2` enabled. To run it:

```bash
docker-compose run --rm backend nmdc-server shell
```

You can also pass `--print-sql` to output all SQL queries.
