import typing

from fastapi import FastAPI

from . import __version__, errors, schemas


def create_app(env: typing.Mapping[str, str]) -> FastAPI:
    app = FastAPI(
        title="NMDC Faceted Search",
        description="Faceted search of the NMDC dataset",
        version=__version__,
    )
    errors.attach_error_handlers(app)

    @app.post(
        "/biosample/search",
        response_model=schemas.SearchResponse,
        tags=["biosample"],
        name="Search for biosamples",
        description="Faceted search of biosample data.",
        responses={
            400: {"description": "The search query was invalid.", "model": schemas.ErrorSchema},
            500: {
                "description": "An unexpected error occurred.",
                "model": schemas.InternalErrorSchema,
            },
        },
    )
    async def search(query: schemas.SearchQuery):
        return {}  # TODO stub

    return app
