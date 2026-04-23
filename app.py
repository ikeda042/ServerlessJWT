from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ValidationError

API_PREFIX = "/api/v1"
JWT_SECRET = "test-only-secret-key"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

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
router = APIRouter(prefix=API_PREFIX)
bearer_scheme = HTTPBearer(auto_error=False)


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


def get_current_account(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if credentials is None:
        raise UNAUTHORIZED_EXCEPTION
    return decode_access_token(credentials.credentials).sub


@router.post("/token", response_model=TokenResponse)
def issue_access_token(payload: LoginRequest) -> TokenResponse:
    if payload.account != TEST_ACCOUNT or payload.password != TEST_PASSWORD:
        raise UNAUTHORIZED_EXCEPTION
    return TokenResponse(access_token=create_access_token(payload.account))


@router.get("/protected", response_model=ProtectedResponse)
def read_protected(current_account: Annotated[str, Depends(get_current_account)]):
    return ProtectedResponse(account=current_account)


app.include_router(router)
