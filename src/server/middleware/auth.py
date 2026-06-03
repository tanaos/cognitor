from collections.abc import Callable, Awaitable
from typing import Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging


logger = logging.getLogger(__name__)

_UNPROTECTED_PREFIXES = (
    # Health check
    "/",
    "/health/ready",
    
    # Docs
    "/docs", "/openapi.json"
)


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
        
        # Always allow health/ping and docs without a token.
        path = request.url.path
        if any(path == p for p in _UNPROTECTED_PREFIXES):
            return await call_next(request)

        if config.MULTI_TENANT:
            # Multi-tenant: resolve the calling user from the API key.
            token = _extract_token(request)
            if not token:
                return _unauthorized()
            authenticator = request.app.state.app_state.authenticator
            if authenticator is None:
                logger.error("Authentication is enabled but no authenticator is configured")
                return JSONResponse(
                    status_code=500,
                    content={"message": "Authentication is not configured"},
                )
            user = await authenticator.authenticate(token)
            if user is None:
                return _unauthorized()
            request.state.current_user = user
            return await call_next(request)

        return await call_next(request)
