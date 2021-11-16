from typing import Any, Dict, Optional
from uuid import UUID

from authlib.integrations import starlette_client
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.oauth2 import OAuth2AuthorizationCodeBearer
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import RedirectResponse

from nmdc_server.config import settings, starlette_config

# A list of orcids with "admin" access to the server.  At some point, we
# may want to add a user table with associated roles to handle this.
_admin_users = {
    "0000-0002-0716-5890",  # Brandon Davis
    "0000-0002-0553-6731",  # Zach Mullen
    "0000-0001-9518-8744",  # David Hays
}

# The type is added to get around an error related to:
#   https://github.com/python/mypy/issues/8477
login_required_responses: Dict[Any, Any] = {
    "401": {"description": "Login required"},
    "403": {"description": "Insufficient permissions"},
}
oauth2_client = starlette_client.OAuth(starlette_config)
oauth2_client.register(
    name="orcid",
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    server_metadata_url=settings.open_id_config_url,
    client_kwargs={
        "scope": settings.oauth_scope,
    },
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=settings.oauth_authorization_endpoint,
    tokenUrl=settings.oauth_token_endpoint,
    scopes={"authorization": settings.oauth_scope},
    auto_error=False,
)


class Token(BaseModel):
    access_token: UUID
    token_type: str
    refresh_token: UUID
    expires_in: int
    scope: str
    name: str
    orcid: str
    expires_at: int


async def get_token(
    request: Request, access_token: Dict[str, Any] = Security(oauth2_scheme)
) -> Optional[Token]:
    token = request.session.get("token")
    if token:
        return Token(**token)
    return None


async def get_current_user(token: Optional[Token] = Depends(get_token)) -> Optional[str]:
    if token:
        return token.name
    return None


async def login_required(token: Optional[Token] = Depends(get_token)) -> Token:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def admin_required(token: Token = Depends(login_required)) -> Token:
    if settings.environment != "production":
        return token
    if token.orcid in _admin_users:
        return token

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Must be a site admin",
    )


router = APIRouter()


# authentication
@router.get("/login", include_in_schema=False)
async def login_via_orcid(request: Request):
    redirect_uri = request.url_for("token")
    if settings.host:
        redirect_uri = f"{settings.host.rstrip('/')}/token"
    return await oauth2_client.orcid.authorize_redirect(request, redirect_uri)


@router.get("/token", name="token", include_in_schema=False)
async def authorize(request: Request):
    token = await oauth2_client.orcid.authorize_access_token(request)
    request.session["token"] = token
    return RedirectResponse(url="/")


@router.get(
    "/logout",
    tags=["user"],
    name="Log out of the current session",
)
async def logout(request: Request):
    request.session.pop("token", None)
    return RedirectResponse(url="/")
