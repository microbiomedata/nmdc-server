FROM tiangolo/uvicorn-gunicorn:python3.9-2023-06-05
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN apt-get update && apt-get install -y postgresql-client

RUN pip install -U pip setuptools wheel
COPY setup.py setup.cfg /app/
RUN pip install -e /app

COPY nmdc_server /app/nmdc_server
COPY .env.production /app/.env
COPY prestart.sh /app/prestart.sh
WORKDIR /app/
ENV MODULE_NAME nmdc_server.asgi
ENV PORT 8000
