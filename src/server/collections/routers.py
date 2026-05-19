from fastapi import APIRouter, status, Request, HTTPException

from .models import ListCollectionsResponse, Collection, CreateCollectionRequest, \
    AddDocumentRequest, AddDocumentResponse, DocumentResponse


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

@collections_router.post(
    path="/{name}/documents",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Document added successfully",
            "content": {
                "application/json": {
                    "example": {"id": 123}
                }
            }
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Collection not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Collection 'nonexistent_collection' does not exist"}
                }
            }
        }
    }
)
async def add_documents(
    name: str,
    request: AddDocumentRequest,
    http_request: Request,
) -> AddDocumentResponse:
    """
    Add a document to the specified collection.
    """
    database = http_request.app.state.database
    try:
        collection = database.get_collection_service(name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Collection '{name}' does not exist"
        )
    document_ids = collection.add_documents(
        vectors=request.vectors,
        metadatas=request.metadata,
    )
    return AddDocumentResponse(ids=document_ids)

@collections_router.get(
    path="/{name}/documents/{id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Document retrieved successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Collection or document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document with id 42 does not exist"}
                }
            }
        }
    }
)
async def get_document(
    name: str,
    id: int,
    http_request: Request,
) -> DocumentResponse:
    """
    Retrieve a document by its ID from the specified collection.
    """
    database = http_request.app.state.database
    try:
        collection = database.get_collection_service(name)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    try:
        vector, metadata = collection.get_document(id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    return DocumentResponse(id=id, vector=vector, metadata=metadata)

@collections_router.delete(
    path="/{name}/documents/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Document deleted successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Collection or document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document with id 42 does not exist"}
                }
            }
        }
    }
)
async def delete_document(
    name: str,
    id: int,
    http_request: Request,
) -> None:
    """
    Delete a document by its ID from the specified collection.
    """
    database = http_request.app.state.database
    try:
        collection = database.get_collection_service(name)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' does not exist"
        )
    try:
        collection.delete_document(id)
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )