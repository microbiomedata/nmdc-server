import typing

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from nmdc_server import __version__, api, auth, errors
from nmdc_server.config import settings


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    app = FastAPI(
        title="NMDC Dataset API",
        version=__version__,
    )

    errors.attach_error_handlers(app)
    app.include_router(api.router, prefix="/api")
    app.include_router(auth.router, prefix="")
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

    return app
