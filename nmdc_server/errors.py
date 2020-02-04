import uuid

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from .utils import log_extras, logger


def attach_error_handlers(app: FastAPI) -> None:
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
