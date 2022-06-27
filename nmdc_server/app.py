import typing

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.sessions import SessionMiddleware

from nmdc_server import __version__, api, auth, errors
from nmdc_server.config import settings


def attach_sentry(app: FastAPI):
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[SqlalchemyIntegration()],
    )
    app.add_middleware(SentryAsgiMiddleware)


def create_app(env: typing.Mapping[str, str], secret_key: str = settings.secret_key) -> FastAPI:
    app = FastAPI(
        title="NMDC Dataset API",
        version=__version__,
    )
    attach_sentry(app)

    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="")
    same_site_value = "lax"
    if settings.environment == "production":
        same_site_value = "Strict"
    app.add_middleware(
        SessionMiddleware,
        secret_key=secret_key,
        https_only=True,
        same_site=same_site_value,
    )

    return app
