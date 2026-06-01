from collections.abc import Callable, Awaitable
import secrets
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

_UNPROTECTED_PREFIXES = ("/", "/auth/", "/health", "/docs", "/openapi.json")


def _extract_token(request: Request) -> Optional[str]:
    return request.headers.get("X-API-Key") or None


def _unauthorized(message: str = "Unauthorized") -> JSONResponse:
    return JSONResponse(
        status_code=401,
        content={"message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        config = request.app.state.app_state.config

        # Always allow health/ping and auth endpoints without a token.
        path = request.url.path
        if any(path.startswith(p) for p in _UNPROTECTED_PREFIXES):
            return await call_next(request)

        if config.multi_tenant:
            # Multi-tenant: resolve the calling user from the API key.
            token = _extract_token(request)
            if not token:
                return _unauthorized()
            user_store = request.app.state.app_state.user_store
            user = user_store.get_user_by_api_key(token)
            if user is None:
                return _unauthorized()
            request.state.current_user = user
            return await call_next(request)

        return await call_next(request)
