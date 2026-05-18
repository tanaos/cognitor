from fastapi import APIRouter, status, Request

from .models import ListCollectionsResponse, Collection, CreateCollectionRequest


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
    collection_entries = database.list_collections()
    collections = [Collection(name=name, dim=dim) for name, dim in collection_entries]
    return ListCollectionsResponse(collections=collections, total=len(collections))

@collections_router.post(
    path="",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Collection created successfully",
            "content": {
                "application/json": {
                    "example": {"name": "new_collection", "dim": 128}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Invalid collection name or dimension, or collection already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Collection 'new_collection' already exists"}
                }
            }
        }
    }
)
async def create_collection(request: Request, collection: CreateCollectionRequest) -> Collection:
    """
    Create a new collection with the specified name and dimensionality.
    """
    database = request.app.state.database
    try:
        database.create_collection(collection.name, collection.dim)
    except ValueError as e:
        raise ValueError(str(e))
    
    return Collection(name=collection.name, dim=collection.dim)