import json
import re
from datetime import datetime
from enum import Enum
from pathlib import PurePath
from typing import Any, Dict

from starlette.requests import Request

from nmdc_server.logger import get_logger

logger = get_logger("nmdc_server")


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
    ip = req.client.host if req.client else ""
    return {
        "ip": ip,
        "method": req.method,
        "url": req.url,
    }


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename according to GCS requirements and recommendations.

    See: https://cloud.google.com/storage/docs/objects#naming

    :param filename: The original filename to sanitize.
    :return: The sanitized filename.
    """
    path = PurePath(filename)

    basename = path.stem
    suffix = path.suffix

    # Remove leading periods
    basename = re.sub(r"^\.+", "", basename)

    # Remove reserved characters
    basename = re.sub(r'[#\[\]*?:"<>|]', "", basename)

    # Remove control characters
    basename = re.sub(r"[\x7F-\x84\x86-\x9F]", "", basename)

    # Remove newline characters
    basename = re.sub(r"[\x0A\x0D]", "", basename)

    combined = basename + suffix

    # Limit to 512 UTF-8 bytes
    utf8_bytes = combined.encode("utf-8")
    max_total_bytes = 512
    total_bytes = len(utf8_bytes)
    if total_bytes > max_total_bytes:
        # Truncate (from the start) to fit within 512 bytes, ensuring we don't cut a multibyte
        # character
        start_byte = total_bytes - max_total_bytes
        # (b & 0xC0) == 0x80 checks if the byte b is a continuation byte in UTF-8
        # https://en.wikipedia.org/wiki/UTF-8#Description
        while start_byte <= total_bytes and (utf8_bytes[start_byte] & 0xC0) == 0x80:
            start_byte += 1
        combined = utf8_bytes[start_byte:].decode("utf-8", errors="ignore")

    return combined
