from typing import Annotated

from anyio.to_thread import run_sync
from fastapi import APIRouter, status, Query, Depends

from .models import ListCollectionsResponse, Collection, CreateCollectionRequest, \
    AddDocumentRequest, AddDocumentResponse, DocumentResponse, UpdateDocumentRequest, \
    ListDocumentsResponse, SearchRequest, SearchResponse, SearchResultResponse
from src.server.dependencies import get_database, get_scheduler, get_embedder_registry, get_config
from src.core.database import Database
from src.execution.batching import batch_add_documents
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.config.settings import Config

DatabaseDep = Annotated[Database, Depends(get_database)]
SchedulerDep = Annotated[CompactionScheduler, Depends(get_scheduler)]
EmbedderRegistryDep = Annotated[EmbedderRegistry, Depends(get_embedder_registry)]
ConfigDep = Annotated[Config, Depends(get_config)]


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
            name=c.name, dim=c.dim, doc_count=c.doc_count, emb_model=c.emb_model
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
    return Collection(
        name=name, dim=coll_info.dim, doc_count=coll_info.doc_count, 
        emb_model=coll_info.emb_model
    )

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
    collection: CreateCollectionRequest, database: DatabaseDep, config: ConfigDep,
    embedder_registry: EmbedderRegistryDep,
) -> Collection:
    """
    Create a new collection with the specified name and dimension.

    ``dim`` may be omitted when ``emb_model`` is set (or a default is configured):
    the server resolves it automatically from the registered embedder.
    """
    emb_model = collection.emb_model or config.default_emb_model
    dim = collection.dim
    if dim is None:
        if not emb_model:
            raise ValueError("dim is required when no emb_model is configured")
        dim = embedder_registry.get(emb_model).dim
    database.create_collection(collection.name, dim, emb_model)
    return Collection(
        name=collection.name, dim=dim, doc_count=0,
        emb_model=emb_model
    )


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
    database.delete_collection(name)


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
    embedder_registry: EmbedderRegistryDep,
) -> AddDocumentResponse:
    """
    Add a document to the specified collection.

    ``vectors`` may be omitted when the collection was created with an
    ``emb_model`` and the corresponding embedder has been registered via
    :func:`src.embeddings.register`.  In that case the server will embed
    ``texts`` automatically before storing them.
    """
    vectors = request.vectors
    if vectors is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "vectors are required when no emb_model is configured for the collection"
            )
        embedder = embedder_registry.get(coll_info.emb_model)
        vectors = embedder.embed(request.texts).tolist()

    collection = database.get_collection_service(name)
    document_ids = collection.add_documents(
        vectors=vectors,
        metadatas=request.metadatas,
        texts=request.texts,
    )
    return AddDocumentResponse(ids=document_ids)


@collections_router.post(
    path="/{name}/documents/bulk",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "description": "Documents added successfully",
            "content": {
                "application/json": {
                    "example": {"ids": ["uuid1", "uuid2", "uuid3"]}
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
async def bulk_add_documents(
    name: str,
    request: AddDocumentRequest,
    database: DatabaseDep,
    embedder_registry: EmbedderRegistryDep,
    batch_size: int = Query(default=512, ge=1, le=4096),
) -> AddDocumentResponse:
    """
    Add a large number of documents to a collection in internal batches.

    Identical request shape to ``POST /{name}/documents`` but processes the
    payload in fixed-size chunks of *batch_size* to keep memory pressure
    bounded when embedding or storing thousands of vectors at once.
    """
    embedder = None
    if request.vectors is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "vectors are required when no emb_model is configured for the collection"
            )
        embedder = embedder_registry.get(coll_info.emb_model)

    collection = database.get_collection_service(name)
    # Run the potentially blocking batch addition in a thread to avoid blocking 
    # the event loop.
    document_ids = await run_sync(
        lambda: batch_add_documents(
            collection=collection,
            texts=request.texts,
            metadatas=request.metadatas,
            vectors=request.vectors,
            embedder=embedder,
            batch_size=batch_size,
        )
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


@collections_router.post(
    path="/{name}/search",
    responses={
        status.HTTP_200_OK: {
            "description": "Search results returned successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Collection not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Collection 'nonexistent_collection' does not exist"}
                }
            }
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Query vector dimension mismatch",
            "content": {
                "application/json": {
                    "example": {"detail": "query vector must have dimension 128"}
                }
            }
        },
    }
)
async def search_collection(
    name: str,
    request: SearchRequest,
    database: DatabaseDep,
    embedder_registry: EmbedderRegistryDep,
) -> SearchResponse:
    """
    Search for the most similar documents to a query vector.

    Either ``query_vector`` or ``query_text`` must be provided.  When only
    ``query_text`` is given the server embeds it automatically using the
    embedder registered for the collection's ``emb_model``.
    Optionally filter results by metadata key-value pairs.
    """
    query_vector = request.query_vector
    if query_vector is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "query_text requires emb_model to be configured for the collection"
            )
        embedder = embedder_registry.get(coll_info.emb_model)
        query_vector = embedder.embed([request.query_text]).tolist()[0]  # type: ignore[arg-type]

    collection = database.get_collection_service(name)
    results = collection.search(
        query_vector=query_vector,
        top_k=request.top_k,
        filters=request.filters,
        include_vectors=request.include_vectors,
    )
    return SearchResponse(
        results=[
            SearchResultResponse(
                id=r.id, score=r.score, text=r.text,
                metadata=r.metadata, vector=r.vector,
            )
            for r in results
        ],
        total=len(results),
    )