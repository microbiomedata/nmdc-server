### Running in Docker

In order to populate the database, you must create a `.env` file in the top
level directory containing mongo credentials.
```
# .env
NMDC_MONGO_USER=changeme
NMDC_MONGO_PASSWORD=changeme
```
With that file in place, populate the docker volume by running,
```
docker-compose run --rm backend nmdc-server migrate
docker-compose run --rm backend nmdc-server ingest
```

Then you can start up the services.
```
docker-compose up
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/docs`.

**NOTE**: If you have migration issues when starting up the server, you can purge the volume and start
from scratch by running:
```
docker-compose down
docker volume rm -f nmdc-server_app-db-data
docker-compose run --rm backend nmdc-server migrate
docker-compose run --rm backend nmdc-server ingest
```


### Development Installation

Requires Python 3.7+

```
pip install -e .
pip install uvicorn tox
```

### Configuration

```
cp .env.example .env
```

Edit values in `.env` to point to existing postgresql databases.

#### OAuth setup

See `nmdc_server/config` for configuration.  Env variable names begin with `NMDC_`.

At minimum, after creating a new OrcID API, you'll need to set these.

```
NMDC_CLIENT_ID=changeme
NMDC_CLIENT_SECRET=changeme
NMDC_HOST=http://localhost:8080
```

### Initialization, migration, and data ingestion

The following commands require credentials to a mongo database hosting the
source data.  Contact Donny for read only access and set variables:
```
NMDC_MONGO_USER=changeme
NMDC_MONGO_PASSWORD=changeme
```

```
nmdc-server truncate
alembic -c nmdc_server/alembic.ini upgrade head
nmdc-server ingest
```

### Run (development)

```
uvicorn nmdc_server.asgi:app --reload
```

View swagger page at `http://localhost:8000/docs`.

### Testing
```
tox
```

### Troubleshooting

Occasionally, a migration will fail to run correctly.  This will cause data ingestion to fail.
The fix is to drop the existing database and to restart the service.  In docker-compose, this
can be done by running
```
docker-compose run backend psql postgres -c 'drop database nmdc;'
```

On Spin, you can use the web interface to start a shell on the `db` instance and run:
```
psql -U postgres postgres -c 'drop database nmdc;'
```
Then, redeploy the backend service.

### Generating new migrations

The way this project [injects](nmdc_server/migrations/env.py) the database uri
into alembic's configuration does not work when using alembic's CLI.  To
generate a new migration, you must modify `nmdc_server/alembic.ini` and hard
code your database uri to `sqlalchemy.url`.  After doing that, you can run alembic
commands as usual, e.g.
```
alembic -c nmdc_server/alembic.ini revision --autogenerate
```
