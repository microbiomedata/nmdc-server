import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel
from pydantic_core import to_jsonable_python
from starlette.requests import Request

from nmdc_server.logger import get_logger

logger = get_logger("nmdc_server")


def json_serializer(data: Any) -> str:
    def default_(val: Any) -> str:
        if isinstance(val, datetime):
            return val.isoformat()
        elif isinstance(val, Enum):
            return val.value
        elif isinstance(val, BaseModel):
            # See:
            # - https://pydantic.dev/docs/validation/latest/api/pydantic-core/pydantic_core/#pydantic_core.to_jsonable_python
            # - https://github.com/pydantic/pydantic/discussions/6652
            return to_jsonable_python(val)
        raise TypeError(f"Cannot serialize {val}")

    return json.dumps(data, default=default_)


def log_extras(req: Request) -> Dict[str, Any]:
    """
    When logging from within a request, pass the Request object here to create the relevant
    logging extras.

    :param req: the current request.
    """
    ip = req.client.host if req.client else ""
    return {
        "ip": ip,
        "method": req.method,
        "url": req.url,
    }
