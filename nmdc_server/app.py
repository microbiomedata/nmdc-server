import typing

import sentry_sdk
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sqlalchemy_oso import SQLAlchemyOso, authorized_sessionmaker
from starlette.middleware.sessions import SessionMiddleware

from nmdc_server import __version__, api, auth, errors, models
from nmdc_server.config import settings


def attach_sentry(app: FastAPI):
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[SqlalchemyIntegration()],
    )


def init_oso(app: FastAPI):
    oso = SQLAlchemyOso(models.Base)
    oso.load_files(["nmdc_server/authorization.polar"])

    return oso


def create_app(env: typing.Mapping[str, str], secure_cookies: bool = True) -> FastAPI:
    app = FastAPI(
        title="NMDC Data and Submission Portal API",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    @app.get("/docs", response_class=RedirectResponse, status_code=301, include_in_schema=False)
    async def redirect_docs():
        return "/api/docs"

    attach_sentry(app)
    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, https_only=secure_cookies)

    return app
