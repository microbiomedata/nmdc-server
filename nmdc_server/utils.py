import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict

from starlette.requests import Request

logger = logging.getLogger("nmdc_server")


def json_serializer(data: Any) -> str:
    def default_(val: Any) -> str:
        if isinstance(val, datetime):
            return val.isoformat()
        elif isinstance(val, Enum):
            return val.value
        raise TypeError(f"Cannot serialize {val}")

    return json.dumps(data, default=default_)


def log_extras(req: Request) -> Dict[str, Any]:
    """
    When logging from within a request, pass the Request object here to create the relevant
    logging extras.

    :param req: the current request.
    """
    return {
        "ip": req.client.host,
        "method": req.method,
        "url": req.url,
    }
