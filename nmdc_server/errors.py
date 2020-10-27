import uuid

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from .query import InvalidAttributeException, InvalidFacetException
from .utils import log_extras, logger


def attach_error_handlers(app: FastAPI) -> None:
    async def handle_custom_validation_error(req: Request, exc: Exception) -> JSONResponse:
        exception_id = str(uuid.uuid4())
        logger.exception("Unhandled exception, ID=%s.", exception_id, extra=log_extras(req))

        return JSONResponse(
            status_code=400,
            content={
                "detail": {
                    "msg": str(exc),
                }
            },
        )

    app.exception_handler(InvalidAttributeException)(handle_custom_validation_error)
    app.exception_handler(InvalidFacetException)(handle_custom_validation_error)

    @app.exception_handler(Exception)
    async def internal_exception_handler(req: Request, exc: Exception) -> JSONResponse:
        exception_id = str(uuid.uuid4())
        logger.exception("Unhandled exception, ID=%s.", exception_id, extra=log_extras(req))

        return JSONResponse(
            status_code=500,
            content={
                "message": "An unexpected error occurred on the server. Details of the error "
                "have been logged.",
                "exception_id": exception_id,
            },
        )
