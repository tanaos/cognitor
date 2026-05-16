from fastapi import APIRouter, status


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