FROM tiangolo/uvicorn-gunicorn:python3.9-2023-06-05
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server
RUN rm /app/main.py

RUN apt-get update && apt-get install -y postgresql-client

RUN pip install -U pip setuptools wheel
COPY . /app/
RUN pip install -e /app

COPY .env.production /app/.env
WORKDIR /app/
ENV MODULE_NAME nmdc_server.asgi
ENV PORT 8000
