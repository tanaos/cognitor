import asyncio

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse


base_router = APIRouter()


@base_router.get(
    path="/",
    responses={
        status.HTTP_200_OK: {
            "description": "Server is up and running",
            "content": {
                "application/json": {
                    "example": {
                        "message": "pong"
                    }
                }
            }
        }
    }
)
async def ping_server() -> str:
    """
    Ping the server
    """
    
    return "pong"


@base_router.get(
    path="/health/ready",
    responses={
        status.HTTP_200_OK: {
            "description": "All models are loaded and the server is ready",
            "content": {
                "application/json": {
                    "example": {"status": "ready"}
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Models are still being loaded",
            "content": {
                "application/json": {
                    "example": {"status": "loading"}
                }
            }
        }
    }
)
async def health_ready(request: Request) -> JSONResponse:
    """
    Return 200 once the application is fully ready to serve requests, or
    503 while it is still loading. Use this as a readiness probe.
    """
    models_ready: asyncio.Event = request.app.state.app_state.models_ready
    if models_ready.is_set():
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ready"})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "loading"}
    )