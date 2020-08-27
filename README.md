### Running in Docker

```
docker-compose up
```

View main application at `http://localhost:8080/` and the swagger page at `http://localhost:8080/docs`.


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

See `nmdc_server/config` for configuration.  Env variable names begin with `nmdc_`.

At minimum, after creating a new OrcID API, you'll need to set these.

```
nmdc_client_id=changeme
nmdc_client_secret=changeme
nmdc_host=http://localhost:8080
```

### Initialization

```
python create_database.py
```

### Apply migrations

If any new migrations have been created, upgrade the schema with
```
alembic upgrade head
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
