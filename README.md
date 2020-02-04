### Installation

Requires Python 3.6+

```
pip install -e .
pip install uvicorn
```

### Run (development)

```
uvicorn nmdc_server.asgi:app --reload
```

Test with `http://localhost:8000/docs`
