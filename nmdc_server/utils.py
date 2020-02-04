import logging
from typing import Any, Dict

from starlette.requests import Request

logger = logging.getLogger("nmdc_server")


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
