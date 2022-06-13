import json
import typing
from base64 import b64decode

import itsdangerous
from itsdangerous.exc import BadSignature
from starlette.datastructures import Secret
from starlette.requests import HTTPConnection
from starlette.types import ASGIApp, Receive, Scope, Send


class AuthMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret_key: typing.Union[str, Secret],
        auth_header: str = "authorization",
        max_age: typing.Optional[int] = 14 * 24 * 60 * 60,  # 14 days, in seconds
    ) -> None:
        self.app = app
        self.signer = itsdangerous.TimestampSigner(str(secret_key))
        self.auth_header = auth_header
        self.max_age = max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:

        connection = HTTPConnection(scope)

        if self.auth_header in connection.headers:
            data = connection.headers[self.auth_header].encode("utf-8")
            try:
                data = self.signer.unsign(data, max_age=self.max_age)
                scope["session"] = json.loads(b64decode(data))
            except BadSignature:
                scope["session"] = {}
        else:
            pass

        await self.app(scope, receive, send)
