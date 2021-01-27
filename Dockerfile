FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev libressl-dev libffi-dev && \
    apk add postgresql-dev postgresql-client && \
    apk add py-cryptography

COPY setup.py setup.cfg /app/
RUN pip install -e /app

COPY nmdc_server /app/nmdc_server
COPY .env.production /app/.env
COPY prestart.sh /app/prestart.sh
WORKDIR /app/
ENV MODULE_NAME nmdc_server.asgi
ENV PORT 8000
