import xml.etree.ElementTree as ElementTree
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, Optional

import requests
from authlib.integrations import starlette_client
from authlib.jose import jwt
from authlib.jose.errors import JoseError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import RedirectResponse

from nmdc_server import crud, models
from nmdc_server.config import settings
from nmdc_server.database import get_db
from nmdc_server.schemas import User

# The type is added to get around an error related to:
#   https://github.com/python/mypy/issues/8477
login_required_responses: Dict[Any, Any] = {
    "401": {"description": "Login required"},
    "403": {"description": "Insufficient permissions"},
}
oauth2_client = starlette_client.OAuth()
oauth2_client.register(
    name="orcid",
    client_id=settings.orcid_client_id,
    client_secret=settings.orcid_client_secret,
    server_metadata_url=settings.orcid_openid_config_url,
    client_kwargs={
        "scope": settings.orcid_authorize_scope,
    },
)

bearer_scheme = HTTPBearer(auto_error=False)

router = APIRouter()

CREDENTIAL_DECODE_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

CREDENTIAL_MISSING_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Login required",
    headers={"WWW-Authenticate": "Bearer"},
)

AUTHORIZATION_CODE_INVALID_EXCEPTION = HTTPException(
    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    detail="Invalid authorization code",
)

API_JWT_ALGORITHM = "HS256"
ORCID_JWT_ISSUER = settings.orcid_base_url  # e.g. "https://orcid.org", "https://sandbox.orcid.org"


class JwtTypes(str, Enum):
    Bearer = "Bearer"
    Refresh = "Refresh"


class TokenRequest(BaseModel):
    code: str
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: bytes
    refresh_token: Optional[bytes] = None
    token_type: str = "bearer"
    expires_in: int


class RefreshRequestBody(BaseModel):
    refresh_token: str


class OidcLoginRequestBody(BaseModel):
    id_token: str


def encode_token(*, data: dict, expires_delta: timedelta) -> bytes:
    """Create a JWT with the given data and expiration.

    In addition to the data, the JWT will include our issuer string (iss), the issuing time (iat),
    and the expiration time (exp). The JWT will be signed with our API's secret key.
    """
    header = {"alg": API_JWT_ALGORITHM, "typ": "JWT"}

    payload = data.copy()
    now = datetime.now(UTC)
    expire = now + expires_delta
    payload.update(
        {
            "iss": settings.host,
            "iat": now,
            "exp": expire,
        }
    )

    return jwt.encode(header, payload, settings.api_jwt_secret)


def decode_token(token: str) -> dict:
    """Decode a JWT and validate its claims.

    The token must have been signed with our API's secret key, must include our issuer string, and
    must not have expired. Once validated, the claims are returned.
    """
    claims_options = {
        "iss": {"essential": True, "value": settings.host},
    }
    claims = jwt.decode(token, settings.api_jwt_secret, claims_options=claims_options)
    claims.validate()
    return claims


def create_token_response(user: models.User, *, create_refresh_token: bool = True) -> TokenResponse:
    """Create a token response for the given user.

    This function generates an access token JWT which includes the user's ID as the subject and
    "Bearer" as the typ. This token will expire in a relatively short time, as defined in the
    settings (24 hours by default). If create_refresh_token is True, a refresh token will also be
    generated. It also has the user's ID as the subject, but the typ is "Refresh" and it will expire
    in a longer time, as defined in the settings (365 days by default).
    """
    token_data = {"sub": str(user.id), "typ": JwtTypes.Bearer}
    expires_delta = timedelta(seconds=settings.api_jwt_expiration)
    access_token = encode_token(data=token_data, expires_delta=expires_delta)
    response = TokenResponse(
        access_token=access_token,
        expires_in=expires_delta.total_seconds(),
    )
    if create_refresh_token:
        token_data["typ"] = JwtTypes.Refresh
        refresh_token = encode_token(
            data=token_data, expires_delta=timedelta(seconds=settings.api_jwt_refresh_expiration)
        )
        response.refresh_token = refresh_token
    return response


def get_user_from_token(db: Session, token: str, token_type: JwtTypes) -> models.User:
    """Get the user associated with the given token.

    This function takes a JWT and first checks to see if it has been manually invalidated. If it has
    not, the token is decoded and its claims are validated by the decode_token function. Next the
    typ is checked against the provided value. Then the user ID is extracted from the sub claim and
    used to retrieve and return the user from the database. If any of these steps fail, an exception
    is raised.
    """
    invalid_token = crud.get_invalidated_token(db, token)
    if invalid_token:
        raise CREDENTIAL_DECODE_EXCEPTION
    try:
        payload = decode_token(token)
        if payload.get("typ") != token_type:
            raise CREDENTIAL_DECODE_EXCEPTION
        user_id = payload.get("sub")
        if user_id is None:
            raise CREDENTIAL_DECODE_EXCEPTION
    except JoseError:
        raise CREDENTIAL_DECODE_EXCEPTION

    user = crud.get_user(db, user_id)
    if user is None:
        raise CREDENTIAL_DECODE_EXCEPTION

    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """Get the current user based on the Bearer credentials."""
    if credentials is None:
        raise CREDENTIAL_MISSING_EXCEPTION
    return get_user_from_token(db, credentials.credentials, JwtTypes.Bearer)


def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> str:
    """Get the current user's access token from the Bearer credentials.

    This function is used to get the access token from the Bearer credentials. The token is
    validated by way of the get_user_from_token function first.
    """
    _ = get_current_user(credentials, db)
    return credentials.credentials


def admin_required(user: models.User = Depends(get_current_user)) -> models.User:
    if settings.environment != "production" and settings.environment != "testing":
        return user
    if user.is_admin:
        return user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Must be a site admin",
    )


@router.get("/login", include_in_schema=False)
async def login_via_orcid(request: Request, redirect_uri: str, state: Optional[str] = None):
    """Initiate the login process via ORCID.

    This route is used to initiate the login process via ORCID. It will redirect the user to ORCID's
    sign in page where they will enter their credentials. The required redirect_uri is **not**
    the one passed to the ORCID /authorize route. Instead, it is stored in the session and used
    later to redirect the user at the very end of the login process. We request that ORCID redirect
    the user back to our /auth/orcid-token route where we complete the ORCID OAuth2 Authorization
    Code Flow.
    """
    allowed_origins = settings.login_redirect_allow_origins.split(",")
    if not any(redirect_uri.startswith(origin) for origin in allowed_origins):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid redirect_uri",
        )
    orcid_redirect_uri = f"{settings.host.rstrip('/')}/auth/orcid-token"
    request.session["redirect_uri"] = redirect_uri
    if state is not None:
        request.session["state"] = state
    return await oauth2_client.orcid.authorize_redirect(request, orcid_redirect_uri)


@router.get("/orcid-token", name="orcid-token", include_in_schema=False)
async def orcid_authorize(request: Request, db: Session = Depends(get_db)):
    """Complete the ORCID OAuth2 Authorization Code Flow and generate our own authorization code.

    This route is used to complete the ORCID OAuth2 Authorization Code Flow. It is provided as the
    redirect_uri in the ORCID /authorize request. The ORCID API will redirect the user back to this
    route with an authorization code. We use this code to request an ORCID access token. The ORCID
    access token response also includes the authenticated user's ORCID iD and name. We use this
    information to create or update a user in our database. Finally, we generate our own
    authorization code and redirect the user back to the original redirect_uri (which was provided
    to the /auth/login route and stored in the session).
    """
    token_response = await oauth2_client.orcid.authorize_access_token(request)
    # TODO: use token_response.access_token to make requests to the ORCID API for more user info?
    # Or possibly store the access token in the database for later use?
    user = User(orcid=token_response["orcid"], name=token_response["name"])
    user_model = crud.get_or_create_user(db, user)

    if not user_model.email:
        # Make API call to ORCID
        orcid_email_response = await oauth2_client.orcid.get(
            f"https://pub.orcid.org/v3.0/{token_response['orcid']}/email",
            token=token_response,
            headers={"Accept": "application/vnd.orcid+json"},
        )

        # JSON data from ORCID API
        email_response_body = orcid_email_response.json()
        
        user_email = None
        for email in email_response_body.get('email', []):
        # Get the first valid email
        # TODO - Consider storing all valid emails in the future
            if email:
                user_email = email.get('email')
                break
        # Assign user email
        user_model.email = user_email

    user_model.name = user.name
    db.commit()

    redirect_uri = request.session.pop("redirect_uri")
    state = request.session.pop("state", None)

    # TODO: also include code_challenge and code_challenge_method in this request to emulate PKCE?

    code = crud.create_authorization_code(db, user_model, redirect_uri)
    url = f"{redirect_uri}?code={code.code}"
    if state is not None:
        url += f"&state={state}"
    return RedirectResponse(url)


@router.post("/token", response_model=TokenResponse, include_in_schema=False)
async def token(
    body: TokenRequest,
    db: Session = Depends(get_db),
):
    """Exchange an nmdc-server authorization code for nmdc-server tokens.

    When a user receives an authorization code from query parameters in the redirect_uri that they
    provided to the /auth/login route, they can exchange it for an nmdc-server access token using
    this route. The provided authorization code is looked up in the database. If it is missing,
    already exchanged, wasn't generated from the same redirect_uri, or is older than 45 seconds, an
    error is raised. Otherwise, the code is marked as exchanged and new tokens are generated for the
    user associated with the code.
    """
    authorization_code = crud.get_authorization_code(db, body.code)
    if (
        authorization_code is None
        or authorization_code.exchanged
        or authorization_code.redirect_uri != body.redirect_uri
        or authorization_code.created < datetime.now(UTC) - timedelta(seconds=45)
    ):
        raise AUTHORIZATION_CODE_INVALID_EXCEPTION
    user = authorization_code.user
    authorization_code.exchanged = True
    db.commit()
    return create_token_response(user)


@lru_cache
def fetch_orcid_jwks():
    """Fetch the JWKS from the ORCID OpenID Connect configuration."""
    orcid_openid_config = requests.get(settings.orcid_openid_config_url).json()
    jwks_uri = orcid_openid_config["jwks_uri"]
    return requests.get(jwks_uri).json()


@router.post("/oidc-login", response_model=TokenResponse, include_in_schema=False)
async def oidc_login(body: OidcLoginRequestBody, db: Session = Depends(get_db)):
    """Exchange an ORCID-issued OpenID Connect token for nmdc-server tokens.

    The endpoint can be used as an alternative to the flow initiated by the /auth/login route. If a
    client has already obtained an OpenID Connect token from ORCID, they can exchange it for a
    nmdc-server tokens using this route. The OIDC token is decoded and validated by looking for
    ORCID as the issuer and the nmdc-server client ID as the audience. If the token is valid, the
    claims in the token are used to create or update a user in the database. Finally, new tokens are
    generated for the user.
    """
    jwks = fetch_orcid_jwks()
    claims_options = {
        "aud": {"essential": True, "value": settings.orcid_client_id},
        "iss": {"essential": True, "value": ORCID_JWT_ISSUER},
    }
    claims = jwt.decode(body.id_token, jwks, claims_options=claims_options)
    claims.validate()
    user = User(orcid=claims["sub"], name=f"{claims['given_name']} {claims['family_name']}")
    user_model = crud.get_or_create_user(db, user)
    user_model.name = user.name
    db.commit()
    return create_token_response(user_model)


@router.post(
    "/refresh",
    include_in_schema=False,
    response_model=TokenResponse,
    response_model_exclude_none=True,
)
async def refresh(body: RefreshRequestBody, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token.

    When a user's access token expires, they can submit a refresh token to this route to receive a
    new access token. The refresh token is first checked to see if it has been manually invalidated.
    Then the refresh token is decoded and validated by the get_user_from_token function. In this
    case only a new access token is generated and returned. The user can continue to use the same
    refresh token to obtain new access tokens until it expires.
    """
    invalid_token = crud.get_invalidated_token(db, body.refresh_token)
    if invalid_token:
        raise CREDENTIAL_DECODE_EXCEPTION
    user = get_user_from_token(db, body.refresh_token, JwtTypes.Refresh)
    return create_token_response(user, create_refresh_token=False)


@router.post("/logout", include_in_schema=False)
async def logout(token: str = Depends(get_current_user_token), db: Session = Depends(get_db)):
    """Log out the current user by invalidating their access token."""
    crud.add_invalidated_token(db, token)
    return {"details": "Logged out successfully"}
