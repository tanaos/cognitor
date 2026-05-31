from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, field_validator

from src.server.dependencies import get_user_store
from src.storage.users import UserStore, UsernameAlreadyExistsError


auth_router = APIRouter()


def _require_user_store(user_store: UserStore = Depends(get_user_store)) -> UserStore:
    if user_store is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Multi-tenant mode is not enabled",
        )
    return user_store


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator("username")
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("username must not be empty")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class AuthResponse(BaseModel):
    api_key: str


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {"api_key": "a3f..."}
                }
            },
        },
        status.HTTP_409_CONFLICT: {
            "description": "Username already exists",
        },
    },
)
async def register(
    body: RegisterRequest,
    user_store: UserStore = Depends(_require_user_store),
) -> AuthResponse:
    """
    Register a new user and return the API key to use for subsequent requests.
    """
    try:
        user = user_store.create_user(body.username, body.password)
    except UsernameAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{body.username}' is already taken",
        )
    return AuthResponse(api_key=user.api_key)


@auth_router.post(
    "/login",
    responses={
        status.HTTP_200_OK: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {"api_key": "a3f..."}
                }
            },
        },
        status.HTTP_401_UNAUTHORIZED: {
            "description": "Invalid credentials",
        },
    },
)
async def login(
    body: RegisterRequest,
    user_store: UserStore = Depends(_require_user_store),
) -> AuthResponse:
    """
    Authenticate with username and password and return the API key.
    """
    user = user_store.verify_credentials(body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return AuthResponse(api_key=user.api_key)
