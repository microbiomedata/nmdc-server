import typing

import sentry_sdk
from fastapi import FastAPI
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.sessions import SessionMiddleware

from nmdc_server import __version__, api, auth, errors
from nmdc_server.auth_middleware import AuthMiddleware
from nmdc_server.config import settings


def attach_sentry(app: FastAPI):
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[SqlalchemyIntegration()],
    )
    app.add_middleware(SentryAsgiMiddleware)


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    app = FastAPI(
        title="NMDC Dataset API",
        version=__version__,
    )
    attach_sentry(app)

    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="")
    app.add_middleware(AuthMiddleware, secret_key=settings.secret_key)
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)
    return app
