from fastapi import APIRouter, status, Request

from .models import ListCollectionsResponse, Collection


collections_router = APIRouter()


@collections_router.get(
    path="",
    responses={
        status.HTTP_200_OK: {
            "description": "List all available collections",
            "content": {
                "application/json": {
                    "example": {
                        "collections": [
                            {"name": "collection1", "description": None},
                            {"name": "collection2", "description": None}
                        ],
                        "total": 2
                    }
                }
            }
        }
    }
)
async def list_collections(request: Request) -> ListCollectionsResponse:
    """
    Get all collections
    """
    database = request.app.state.database
    collection_names = database.list_collections()
    collections = [Collection(name=name) for name in collection_names]
    return ListCollectionsResponse(collections=collections, total=len(collections))