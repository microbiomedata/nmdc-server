from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from authlib.integrations import starlette_client
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.oauth2 import OAuth2AuthorizationCodeBearer
from jose import jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from nmdc_server import crud, models
from nmdc_server.config import settings, starlette_config
from nmdc_server.database import get_db
from nmdc_server.schemas import User

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
    request: Request, token: Optional[str] = Security(oauth2_scheme)
) -> Optional[Token]:
    session_token = request.session.get("token")
    if session_token:
        return Token(**session_token)
    if token:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return Token(**payload)
    return None


async def get_current_user(token: Optional[Token] = Depends(get_token)) -> Optional[str]:
    if token:
        return token.name
    return None


async def get_current_user_orcid(token: Optional[Token] = Depends(get_token)) -> Optional[str]:
    if token:
        return token.orcid
    return None


async def login_required(
    token: Optional[Token] = Depends(get_token), db: Session = Depends(get_db)
) -> models.User:
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_schema = User(name=token.name, orcid=token.orcid)
    return crud.get_or_create_user(db, user_schema)


async def admin_required(user: models.User = Depends(login_required)) -> models.User:
    if settings.environment != "production" and settings.environment != "testing":
        return user
    if user.is_admin:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Must be a site admin",
    )


def encode_token(data: dict):
    encoded_jwt = jwt.encode(data, settings.secret_key, algorithm="HS256")
    return encoded_jwt


router = APIRouter()


class LoginBehavior(str, Enum):
    web = "web"
    jwt = "jwt"
    app = "app"


# authentication
@router.get("/login", include_in_schema=False)
async def login_via_orcid(request: Request, behavior: LoginBehavior = LoginBehavior.web):
    qs = f"?behavior={behavior}"
    if settings.host:
        redirect_uri = f"{settings.host.rstrip('/')}/token{qs}"
    else:
        redirect_uri = request.url_for("token") + qs
    return await oauth2_client.orcid.authorize_redirect(request, redirect_uri)


@router.get("/token", name="token", include_in_schema=False)
async def authorize(
    request: Request, db: Session = Depends(get_db), behavior: LoginBehavior = LoginBehavior.web
):
    token = await oauth2_client.orcid.authorize_access_token(request)
    user = User(orcid=token["orcid"], name=token["name"])
    user_model = crud.get_or_create_user(db, user)
    user_model.name = user.name
    db.commit()
    if behavior == LoginBehavior.web:
        request.session["token"] = token
        return RedirectResponse(url="/")
    if behavior == LoginBehavior.jwt:
        return encode_token(token)
    if behavior == LoginBehavior.app:
        return RedirectResponse(
            url=f"{settings.field_notes_host}/token?token=" + encode_token(token)
        )


@router.get(
    "/logout",
    tags=["user"],
    name="Log out of the current session",
)
async def logout(request: Request):
    request.session.pop("token", None)
    return RedirectResponse(url="/")
