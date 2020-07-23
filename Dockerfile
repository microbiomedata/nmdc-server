FROM tiangolo/uvicorn-gunicorn:python3.8-alpine3.10

RUN apk update && \
    apk add --virtual build-deps gcc python-dev musl-dev && \
    apk add postgresql-dev postgresql-client && \
    apk add curl

COPY . /app
COPY .env.production /app/.env
WORKDIR /app/
ENV MODULE_NAME nmdc_server.asgi
ENV PORT 8000

RUN pip install -e /app

