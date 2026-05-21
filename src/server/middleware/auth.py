from collections.abc import Callable, Awaitable
import secrets
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


def _extract_token(request: Request) -> Optional[str]:
    authorization: str = request.headers.get("Authorization", "")
    if authorization.lower().startswith("bearer "):
        return authorization[7:]
    return request.headers.get("X-API-Key") or None


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """
        Middleware to enforce API key authentication if enabled in the configuration.
        """
        
        if not request.app.state.app_state.config.auth_enabled:
            return await call_next(request)

        token = _extract_token(request)
        expected: str = request.app.state.app_state.config.api_key

        if not token or not expected or not secrets.compare_digest(token, expected):
            return JSONResponse(
                status_code=401,
                content={"message": "Unauthorized"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)