### Running in Docker

```
docker-compose up
```

View swagger page at `http://localhost:8000/docs`.


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
