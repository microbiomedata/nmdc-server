import typing

from fastapi import FastAPI

from . import __version__, api, errors


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    app = FastAPI(
        title="NMDC Faceted Search",
        description="Faceted search of the NMDC dataset",
        version=__version__,
    )
    errors.attach_error_handlers(app)
    app.include_router(api.router)

    return app
