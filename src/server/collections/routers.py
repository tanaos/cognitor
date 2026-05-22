from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Query, Depends

from .models import ListCollectionsResponse, Collection, CreateCollectionRequest, \
    AddDocumentRequest, AddDocumentResponse, DocumentResponse, UpdateDocumentRequest, \
    ListDocumentsResponse
from src.server.dependencies import get_database, get_scheduler
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler

DatabaseDep = Annotated[Database, Depends(get_database)]
SchedulerDep = Annotated[CompactionScheduler, Depends(get_scheduler)]


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
                                {"name": "collection1", "dim": 128, "doc_count": 42},
                                {"name": "collection2", "dim": 256, "doc_count": 7}
                            ],
                        "total": 2
                    }
                }
            }
        }
    }
)
async def list_collections(database: DatabaseDep) -> ListCollectionsResponse:
    """
    Get all collections
    """
    collection_entries = database.list_collections()
    collections = [
        Collection(
            name=c.name, dim=c.dim, doc_count=c.doc_count
        ) for c in collection_entries
    ]
    return ListCollectionsResponse(collections=collections, total=len(collections))

@collections_router.get(
    path="/{name}",
    responses={
        status.HTTP_200_OK: {
            "description": "Get collection details",
            "content": {
                "application/json": {
                    "example": {"name": "collection1", "dim": 128, "doc_count": 42}
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
async def get_collection(name: str, database: DatabaseDep) -> Collection:
    """
    Get a collection by name.
    """
    coll_info = database.get_collection_info(name)
    return Collection(name=name, dim=coll_info.dim, doc_count=coll_info.doc_count)

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
            "description": "Invalid collection name or dimension",
            "content": {
                "application/json": {
                    "example": {"detail": "dim must be a positive integer"}
                }
            }
        },
        status.HTTP_409_CONFLICT: {
            "description": "Collection already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Collection 'new_collection' already exists"}
                }
            }
        }
    }
)
async def create_collection(
    collection: CreateCollectionRequest, database: DatabaseDep
) -> Collection:
    """
    Create a new collection with the specified name and dimensionality.
    """
    database.create_collection(collection.name, collection.dim)
    return Collection(name=collection.name, dim=collection.dim, doc_count=0)


@collections_router.delete(
    path="/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Collection deleted successfully",
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
async def delete_collection(name: str, database: DatabaseDep) -> None:
    """
    Delete a collection by name.
    """
    deleted = database.delete_collection(name)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' does not exist"
        )


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
        },
    }
)
async def add_documents(
    name: str,
    request: AddDocumentRequest,
    database: DatabaseDep,
) -> AddDocumentResponse:
    """
    Add a document to the specified collection.
    """
    collection = database.get_collection_service(name)
    document_ids = collection.add_documents(
        vectors=request.vectors,
        metadatas=request.metadatas,
        texts=request.texts,
    )
    return AddDocumentResponse(ids=document_ids)


@collections_router.get(
    path="/{name}/documents",
    responses={
        status.HTTP_200_OK: {
            "description": "Documents retrieved successfully",
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
async def list_documents(
    name: str,
    database: DatabaseDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=1000),
) -> ListDocumentsResponse:
    """
    Retrieve paginated documents from the specified collection.
    """
    coll_info = database.get_collection_info(name)
    collection = database.get_collection_service(name)

    docs = collection.list_documents(offset=offset, limit=limit)
    documents = [
        DocumentResponse(id=doc.id, vector=doc.vector, text=doc.text, metadata=doc.metadata)
        for doc in docs
    ]
    return ListDocumentsResponse(
        documents=documents,
        total=coll_info.doc_count,
        offset=offset,
        limit=limit,
    )


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
    id: str,
    database: DatabaseDep,
) -> DocumentResponse:
    """
    Retrieve a document by its ID from the specified collection.
    """
    collection = database.get_collection_service(name)
    doc = collection.get_document(id)
    return DocumentResponse(
        id=doc.id, vector=doc.vector, text=doc.text, metadata=doc.metadata
    )


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
    id: str,
    database: DatabaseDep,
    scheduler: SchedulerDep,
) -> None:
    """
    Delete a document by its ID from the specified collection.
    """
    collection = database.get_collection_service(name)
    collection.delete_document(id)

    # After a deletion, check if the collection has reached the compaction threshold and 
    # schedule compaction if needed.
    await scheduler.check_and_schedule(name)


# TODO: if metadata end up being stored as vectors, this endpoint should be deleted
@collections_router.patch(
    path="/{name}/documents/{id}/metadata",
    responses={
        status.HTTP_200_OK: {
            "description": "Document metadata updated successfully",
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
async def update_document_metadata(
    name: str,
    id: str,
    request: UpdateDocumentRequest,
    database: DatabaseDep,
) -> DocumentResponse:
    """
    Replace the metadata of a document by its ID.
    """
    collection = database.get_collection_service(name)
    collection.update_document(id, request.metadata)
    doc = collection.get_document(id)
    return DocumentResponse(
        id=id, vector=doc.vector, text=doc.text, metadata=doc.metadata
    )