import logging
import typing
from contextlib import asynccontextmanager

import sentry_sdk
from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from starlette.middleware.sessions import SessionMiddleware

from nmdc_server import __version__, api, auth, errors
from nmdc_server.config import settings
from nmdc_server.static_files import generate_submission_schema_files, initialize_static_directory


def attach_sentry(app: FastAPI):
    if not settings.sentry_dsn:
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[
            LoggingIntegration(level=logging.INFO, event_level=logging.WARNING),
            SqlalchemyIntegration(),
        ],
        in_app_include=["nmdc_server"],
        attach_stacktrace=True,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=1,
    )


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    def generate_and_mount_static_files():
        static_path = initialize_static_directory(remove_existing=True)
        generate_submission_schema_files(directory=static_path)
        app.mount("/static", StaticFiles(directory=static_path), name="static")

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        generate_and_mount_static_files()
        yield

    app = FastAPI(
        title="NMDC Data and Submission Portal API",
        description="""
To use authenticated endpoints, you must first obtain an Access Token by following the
instructions in the Developer Tools section <a href="/user">here</a>. Once you have an Access
Token, click the "Authorize" button on this page. In the popup, paste the token in the "Value"
field and click "Authorize".
""",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        debug=settings.debug,
        lifespan=lifespan,
    )
    if settings.environment == "development":
        app.add_middleware(DebugToolbarMiddleware)

    @app.get("/docs", response_class=RedirectResponse, status_code=301, include_in_schema=False)
    async def redirect_docs():
        return "/api/docs"

    attach_sentry(app)
    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="/auth")
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins.split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
