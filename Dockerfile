FROM python:3.12-slim
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN apt clean
RUN apt-get upgrade
RUN apt-get update 
RUN apt-get install -y postgresql-client git libpq-dev libc6-dev gcc

RUN pip install -U pip setuptools wheel
COPY . /app/
RUN pip install -e /app

COPY .env.production /app/.env
RUN chmod +x /app/start.sh
WORKDIR /app/
CMD ["/app/start.sh"]
