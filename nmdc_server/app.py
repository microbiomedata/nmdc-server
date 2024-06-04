import typing

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
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
        integrations=[SqlalchemyIntegration()],
        enable_tracing=True,
        traces_sample_rate=0.25,
    )


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

    @app.on_event("startup")
    async def generate_and_mount_static_files():
        static_path = initialize_static_directory(remove_existing=True)
        generate_submission_schema_files(directory=static_path)
        app.mount("/static", StaticFiles(directory=static_path), name="static")

    attach_sentry(app)
    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, https_only=secure_cookies)

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins.split(","),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app
