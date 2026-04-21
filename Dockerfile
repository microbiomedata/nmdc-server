FROM python:3.12-slim-bookworm
LABEL org.opencontainers.image.source=https://github.com/microbiomedata/nmdc-server

RUN apt clean
RUN apt-get upgrade
RUN apt-get update
# Keep the postgres-client version in sync with:
#   - .github/workflows/server.yml
#   - docker-compose.yml
RUN apt-get install -y postgresql-client-15 git libpq-dev libc6-dev gcc

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1

# Install the project's dependencies from the lockfile and cache
# the environment in a dedicated layer.
WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project

# Install the project itself.
COPY . /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

COPY .env.production /app/.env
RUN chmod +x /app/start.sh
WORKDIR /app/
CMD ["uv", "run", "/app/start.sh"]
