from datetime import datetime, timedelta, timezone
from typing import Any, Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, Field, ValidationError

API_PREFIX = "/api/v1"
TEST_API_PREFIX = f"{API_PREFIX}/test"
JWT_SECRET = "test-only-secret-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
SUPPORTED_SIGNING_ALGORITHMS = {"HS256", "RS256"}
DEFAULT_JWT_ISSUER = "https://jwt.ikeda042.home/api/v1/"
DEFAULT_JWT_EXPIRE_HOURS = 1
DEFAULT_JWT_USER_NAME = "ikeda042"
DEFAULT_JWT_SCOPE = "admin"

TEST_ACCOUNT = "test-user"
TEST_PASSWORD = "test-password"

UNAUTHORIZED_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid authentication credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

app = FastAPI(
    title="Serverless JWT API",
    version="1.0.0",
    docs_url=f"{API_PREFIX}/docs",
    openapi_url=f"{API_PREFIX}/openapi.json",
    redoc_url=None,
)
production_router = APIRouter(prefix=API_PREFIX)
test_router = APIRouter(prefix=TEST_API_PREFIX)
bearer_scheme = HTTPBearer(auto_error=False)


def create_default_jwt_payload() -> dict[str, Any]:
    expires_at = datetime.now(timezone.utc) + timedelta(hours=DEFAULT_JWT_EXPIRE_HOURS)
    return {
        "iss": DEFAULT_JWT_ISSUER,
        "exp": int(expires_at.timestamp()),
        "user_name": DEFAULT_JWT_USER_NAME,
        "scope": DEFAULT_JWT_SCOPE,
    }


class LoginRequest(BaseModel):
    account: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int


class ProtectedResponse(BaseModel):
    account: str


class JwtCreateRequest(BaseModel):
    alg: str
    signing_key: str
    payload: dict[str, Any] = Field(
        default_factory=create_default_jwt_payload,
        json_schema_extra={"example": create_default_jwt_payload()},
    )


class JwtCreateResponse(BaseModel):
    token: str
    alg: str


class JwtVerifyResponse(BaseModel):
    valid: bool
    alg: str
    payload: dict[str, Any]


def create_access_token(account: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": account,
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenPayload(**payload)
    except (JWTError, ValidationError) as exc:
        raise UNAUTHORIZED_EXCEPTION from exc


def validate_signing_algorithm(alg: str) -> str:
    if alg not in SUPPORTED_SIGNING_ALGORITHMS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported alg. Use HS256 or RS256.",
        )
    return alg


def create_signed_jwt(payload: dict[str, Any], signing_key: str, alg: str) -> str:
    try:
        return jwt.encode(payload, signing_key, algorithm=validate_signing_algorithm(alg))
    except (JWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create JWT with the provided signing key or payload.",
        ) from exc


def verify_signed_jwt(token: str, verification_key: str, alg: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            verification_key,
            algorithms=[validate_signing_algorithm(alg)],
        )
    except (JWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to verify JWT with the provided verification key or token.",
        ) from exc


def get_current_account(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if credentials is None:
        raise UNAUTHORIZED_EXCEPTION
    return decode_access_token(credentials.credentials).sub


@production_router.post("/token", response_model=JwtCreateResponse)
def issue_custom_jwt(payload: JwtCreateRequest) -> JwtCreateResponse:
    return JwtCreateResponse(
        token=create_signed_jwt(
            payload=payload.payload,
            signing_key=payload.signing_key,
            alg=payload.alg,
        ),
        alg=payload.alg,
    )


@production_router.get("/token", response_model=JwtVerifyResponse)
def verify_custom_jwt(
    token: Annotated[str, Query(description="JWT to verify")],
    alg: Annotated[str, Query(description="Expected signing algorithm: HS256 or RS256")],
    verification_key: Annotated[
        str,
        Query(
            description=(
                "Verification key. Use the shared secret for HS256 or the public key "
                "for RS256."
            ),
        ),
    ],
) -> JwtVerifyResponse:
    return JwtVerifyResponse(
        valid=True,
        alg=alg,
        payload=verify_signed_jwt(
            token=token,
            verification_key=verification_key,
            alg=alg,
        ),
    )


@test_router.post("/token", response_model=TokenResponse)
def issue_access_token(payload: LoginRequest) -> TokenResponse:
    if payload.account != TEST_ACCOUNT or payload.password != TEST_PASSWORD:
        raise UNAUTHORIZED_EXCEPTION
    return TokenResponse(access_token=create_access_token(payload.account))


@test_router.get("/protected", response_model=ProtectedResponse)
def read_protected(current_account: Annotated[str, Depends(get_current_account)]):
    return ProtectedResponse(account=current_account)


app.include_router(production_router)
app.include_router(test_router)
