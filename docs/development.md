# Development Setup

## Docker

Install docker and docker-compose.

## Configuration

```bash
cp .env.example .env
```

Edit values in `.env` to point to existing postgresql databases. See `nmdc_server/config.py` for all configuration variables.  Variable names in `.env` should be all uppercase and prefixed with `NMDC_`.

## OAuth setup

1. Create an OrcID account at [orcid.org](https://orcid.org).
1. Create an Application via the OrcID [developer tools](https://orcid.org/developer-tools) page.
    - Set the Redirect URIs (the first and only one) to `http://127.0.0.1:8080`
        - Note: OrcID has changed the validation logic for this form field over time.
        - In case you run into validation errors, you may find [this issue](https://github.com/microbiomedata/nmdc-server/issues/1041) helpful.
    - You will use the resulting **Client ID** and **Client Secret** in the next step.
1. Set the following configuration in `.env`, and then restart the stack.

```bash
NMDC_CLIENT_ID=changeme
NMDC_CLIENT_SECRET=changeme
NMDC_HOST=http://localhost:8080
```

# Load production data

The `nmdc-server` CLI has a `load-db` subcommand which populates your local database using a nightly production backup. These backups are stored on NERSC. You must have NERSC credentials to use this subcommand.

First use NERSC's `sshproxy` [tool](https://docs.nersc.gov/connect/mfa/#sshproxy) to generate an ssh key.

```bash
sshproxy.sh -u <nersc_username>
```

Then run the `load-db` subcommand from a `backend` container, mounting the ssh key.

```bash
docker compose run \
  --rm \
  -v ~/.ssh/nersc:/tmp/nersc \
  backend \
  nmdc-server load-db -u <nersc_username>
```

To see all CLI options run:

```bash
nmdc-server load-db --help
```

**Note**: if you already have a local database set up, the first time you attempt to load from a production backup you may see an error about a missing `nmdc_data_reader` role. If you see this error, run the following command to remove existing docker volumes:

```bash
docker compose down -v
```

This should only need to be done once. When the `db` service starts up again (including via running the `load-db` command), the necessary roles and databases will be created automatically.

# Running the server

```bash
docker-compose up -d
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/api/docs`.



## Outside Docker

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

View swagger page at `http://localhost:8000/api/docs`.



# Running ingest

You need an active SSH tunnel connection to NERSC attached to the compose network.  After running docker-compose up, run this container.

If you haven't already, [set up MFA on your NERSC account](https://docs.nersc.gov/connect/mfa/) (it's required for SSHing in).

```bash
export NERSC_USER=changeme
docker run --rm -it -p 27017:27017 --network nmdc-server_default --name tunnel kroniak/ssh-client ssh -o StrictHostKeyChecking=no -L 0.0.0.0:27017:mongo-loadbalancer.nmdc.production.svc.spin.nersc.org:27017 $NERSC_USER@dtn01.nersc.gov '/bin/bash -c "while [[ 1 ]]; do echo heartbeat; sleep 300; done"'
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
docker-compose run backend nmdc-server ingest -vv --function-limit 100
```

# Running the client

Run the client in development mode.

``` bash
cd web/
yarn
yarn serve
```

**Note**: To authenticate, log into the portal at `http://localhost:8080` first.  Then, the dev environment portal at `http://localhost:8081` will also be authenticated.  This is because oauth with webpack dev server is not possible.

# Testing

```bash
tox
```

# Generating new migrations

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

# Developing with the shell

A handy IPython shell is provided with some commonly used symbols automatically
imported, and `autoreload 2` enabled. To run it:

```bash
docker-compose run --rm backend nmdc-server shell
```

You can also pass `--print-sql` to output all SQL queries.
