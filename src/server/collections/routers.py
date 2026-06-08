from typing import Annotated, Optional
from anyio.to_thread import run_sync
from fastapi import APIRouter, status, Query, Depends

from .models import ListCollectionsResponse, Collection, CreateCollectionRequest, \
    AddDocumentRequest, AddDocumentResponse, DocumentResponse, UpdateDocumentRequest, \
    ListDocumentsResponse, SearchRequest, SearchResponse, SearchResultResponse, AnswerPassage, \
    BulkAddDocumentRequest
from src.server.dependencies import (
    get_database,
    get_scheduler,
    get_embedder_registry,
    get_qa_extractor,
    get_reranker,
    get_config,
    get_models_ready,
    get_telemetry_client,
)
from src.core.database import Database
from src.execution.async_tasks import bulk_ingest
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.config.settings import Config
from src.search.extractive_qa import ExtractiveQA
from src.search.rerank import Reranker
from src.telemetry.client import TelemetryClient
from src.telemetry.events import (
    CollectionCreated,
    CollectionDeleted,
    DocumentDeleted,
    DocumentsAdded,
    SearchPerformed,
)
import asyncio
import logging
import time


_logger = logging.getLogger(__name__)


DatabaseDep = Annotated[Database, Depends(get_database)]
SchedulerDep = Annotated[CompactionScheduler, Depends(get_scheduler)]
EmbedderRegistryDep = Annotated[EmbedderRegistry, Depends(get_embedder_registry)]
QaExtractorDep = Annotated[ExtractiveQA, Depends(get_qa_extractor)]
RerankerDep = Annotated[Reranker, Depends(get_reranker)]
ConfigDep = Annotated[Config, Depends(get_config)]
ModelsReadyDep = Annotated[asyncio.Event, Depends(get_models_ready)]
TelemetryDep = Annotated[TelemetryClient, Depends(get_telemetry_client)]


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
    embedder_registry: EmbedderRegistryDep, models_ready: ModelsReadyDep,
    telemetry: TelemetryDep,
) -> Collection:
    """
    Create a new collection with the specified name and dimension.

    ``dim`` may be omitted when ``emb_model`` is set (or a default is configured):
    the server resolves it automatically from the registered embedder.
    """
    emb_model = collection.emb_model or config.DEFAULT_EMB_MODEL
    dim = collection.dim
    if dim is None:
        if not emb_model:
            raise ValueError("dim is required when no emb_model is configured")
        await models_ready.wait()
        dim = embedder_registry.get(emb_model).dim
    database.create_collection(collection.name, dim, emb_model)
    telemetry.enqueue(CollectionCreated(dim=dim, has_emb_model=bool(emb_model)))
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
async def delete_collection(name: str, database: DatabaseDep, telemetry: TelemetryDep) -> None:
    """
    Delete a collection by name.
    """
    database.delete_collection(name)
    telemetry.enqueue(CollectionDeleted())


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
    scheduler: SchedulerDep,
    models_ready: ModelsReadyDep,
    telemetry: TelemetryDep,
) -> AddDocumentResponse:
    """
    Add a document to the specified collection.

    ``vectors`` may be omitted when the collection was created with an
    ``emb_model`` and the corresponding embedder has been registered via
    :func:`src.embeddings.register`.  In that case the server will embed
    ``texts`` automatically before storing them.
    """
    t0 = time.monotonic()
    # Embed outside the lock — it's CPU-bound and does not touch shared storage.
    vectors = request.vectors
    used_embedding = vectors is None
    if vectors is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "vectors are required when no emb_model is configured for the collection"
            )
        await models_ready.wait()
        embedder = embedder_registry.get(coll_info.emb_model)
        vectors = embedder.embed(request.texts).tolist()

    collection = database.get_collection_service(name)
    async with scheduler.get_collection_lock(str(database.root_path / name)):
        document_ids = collection.add_documents(
            vectors=vectors,
            metadatas=request.metadatas,
            texts=request.texts,
        )
    telemetry.enqueue(DocumentsAdded(
        count=len(document_ids),
        used_embedding=used_embedding,
        duration_ms=(time.monotonic() - t0) * 1000,
    ))
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
    request: BulkAddDocumentRequest,
    database: DatabaseDep,
    embedder_registry: EmbedderRegistryDep,
    scheduler: SchedulerDep,
    models_ready: ModelsReadyDep,
    telemetry: TelemetryDep,
    batch_size: int = Query(default=512, ge=1, le=4096),
) -> AddDocumentResponse:
    """
    Add a large number of documents to a collection in internal batches.

    Identical request shape to ``POST /{name}/documents`` but processes the
    payload in fixed-size chunks of *batch_size* to keep memory pressure
    bounded when embedding or storing thousands of vectors at once.
    """
    t0 = time.monotonic()
    used_embedding = request.vectors is None
    embedder = None
    if request.vectors is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "vectors are required when no emb_model is configured for the collection"
            )
        await models_ready.wait()
        embedder = embedder_registry.get(coll_info.emb_model)

    collection = database.get_collection_service(name)
    document_ids = await bulk_ingest(
        collection=collection,
        lock_key=str(database.root_path / name),
        scheduler=scheduler,
        texts=request.texts,
        metadatas=request.metadatas,
        vectors=request.vectors,
        embedder=embedder,
        batch_size=batch_size,
    )
    telemetry.enqueue(DocumentsAdded(
        count=len(document_ids),
        used_embedding=used_embedding,
        duration_ms=(time.monotonic() - t0) * 1000,
    ))
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
    include_vectors: bool = Query(default=False),
) -> ListDocumentsResponse:
    """
    Retrieve paginated documents from the specified collection.
    """
    collection = database.get_collection_service(name, load_index=False)
    docs = collection.list_documents(
        offset=offset,
        limit=limit,
        include_vectors=include_vectors,
    )
    documents = [
        DocumentResponse(id=doc.id, vector=doc.vector, text=doc.text, metadata=doc.metadata)
        for doc in docs
    ]
    return ListDocumentsResponse(
        documents=documents,
        total=database.get_collection_info(name).doc_count,
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
    scheduler: SchedulerDep,
) -> DocumentResponse:
    """
    Retrieve a document by its ID from the specified collection.
    """
    collection = database.get_collection_service(name)
    async with scheduler.get_collection_lock(str(database.root_path / name)):
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
    telemetry: TelemetryDep,
) -> None:
    """
    Delete a document by its ID from the specified collection.
    """
    collection = database.get_collection_service(name)
    async with scheduler.get_collection_lock(str(database.root_path / name)):
        collection.delete_document(id)

    # check_and_schedule is called outside the lock: it inspects lock.locked() to
    # decide whether to enqueue a compaction task. Calling it while holding the
    # lock would make it always see the lock as taken and never schedule.
    await scheduler.check_and_schedule(name, database)
    telemetry.enqueue(DocumentDeleted())


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
    scheduler: SchedulerDep,
) -> DocumentResponse:
    """
    Replace the metadata of a document by its ID.
    """
    collection = database.get_collection_service(name)
    async with scheduler.get_collection_lock(str(database.root_path / name)):
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
    qa_extractor: QaExtractorDep,
    reranker: RerankerDep,
    scheduler: SchedulerDep,
    models_ready: ModelsReadyDep,
    telemetry: TelemetryDep,
) -> SearchResponse:
    """
    Search for the most similar documents to a query vector.

    Either ``query_vector`` or ``query_text`` must be provided.  When only
    ``query_text`` is given the server embeds it automatically using the
    embedder registered for the collection's ``emb_model``.
    Optionally filter results by metadata key-value pairs.
    """
    t0 = time.monotonic()
    # Embed outside the lock — it's CPU-bound and does not touch shared storage.
    query_vector = request.query_vector
    if query_vector is None:
        coll_info = database.get_collection_info(name)
        if not coll_info.emb_model:
            raise ValueError(
                "query_text requires emb_model to be configured for the collection"
            )
        await models_ready.wait()
        embedder = embedder_registry.get(coll_info.emb_model)
        query_vector = embedder.embed([request.query_text]).tolist()[0]  # type: ignore[arg-type]

    collection = database.get_collection_service(name)
    async with scheduler.get_collection_lock(str(database.root_path / name)):
        results = collection.search(
            query_vector=query_vector,
            top_k=request.top_k,
            filters=request.filters,
            include_vectors=request.include_vectors,
        )

    # Reranking is only applied when:
    # - the query is textual (reranking a pure vector query would not make sense)
    # - there are results to rerank (skip the step when there are no matches)
    # - the client has not explicitly disabled it (it can be costly, so we want to allow skipping it)
    if request.query_text is not None and results and request.perform_reranking:
        try:
            results = await run_sync(reranker.rerank, request.query_text, results)
        except Exception:
            _logger.exception("Reranking failed for collection: %s", name)

    # Extractive QA is only applied when:
    # - the query is textual (it would not make sense to extract an answer from a non-textual query)
    # - there are results to extract from (skip the step when there are no matches)
    # - the client has not explicitly disabled it (it can be costly, so we want to allow skipping it)
    answers: list[Optional[AnswerPassage]] = [None] * len(results)
    if request.query_text is not None and results and request.perform_extractive_qa:
        try:
            extracted_answers = await run_sync(
                qa_extractor.extract_many,
                request.query_text,
                [result.text for result in results],
            )
            for idx, extracted in enumerate(extracted_answers):
                if extracted is None:
                    continue
                answers[idx] = AnswerPassage(
                    passage=extracted.passage,
                    start=extracted.start,
                    end=extracted.end,
                )
        except Exception:
            _logger.exception("Extractive QA inference failed for collection: %s", name)

    telemetry.enqueue(SearchPerformed(
        duration_ms=(time.monotonic() - t0) * 1000,
        top_k=request.top_k,
        result_count=len(results),
        used_filters=bool(request.filters),
        used_query_text=request.query_text is not None,
        reranking_applied=request.perform_reranking,
        extractive_qa_applied=request.perform_extractive_qa,
    ))
    return SearchResponse(
        results=[
            SearchResultResponse(
                id=r.id, score=r.score, text=r.text,
                metadata=r.metadata, vector=r.vector,
                answer=answers[idx],
            )
            for idx, r in enumerate(results)
        ],
        total=len(results),
    )