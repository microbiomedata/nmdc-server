FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev libressl-dev libffi-dev g++ && \
    apk add postgresql-dev postgresql-client && \
    apk add py-cryptography

RUN pip install -U pip
COPY setup.py setup.cfg /app/
RUN pip install -e /app

COPY nmdc_server /app/nmdc_server
COPY .env.production /app/.env
COPY prestart.sh /app/prestart.sh
WORKDIR /app/
ENV MODULE_NAME nmdc_server.asgi
ENV PORT 8000
