import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional
from anyio.to_thread import run_sync
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ValidationException
from fastapi.openapi.utils import get_openapi
import traceback

from .base.routers import base_router
from .collections.routers import collections_router
from .admin.routers import admin_router
from .auth.service import build_authenticator
from .responses import ErrorResponse
from .middleware.auth import AuthMiddleware

from src.utils.logging import setup_logging
from src.config.settings import get_config
from src.core.database import Database
from src.core.state import AppState
from src.execution.scheduler import CompactionScheduler
from src.core.exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    DocumentNotFoundError,
    InvalidCollectionNameError,
    InvalidDimensionError,
    InvalidDocumentInputError,
    DimensionMismatchError,
)
from src.embeddings.registry import EmbedderRegistry
from src.embeddings.exceptions import EmbedderNotFoundError, EmbeddingError
from src.search.extractive_qa import ExtractiveQA
from src.search.rerank import Reranker
from src.telemetry.client import TelemetryClient, resolve_instance_id
from src.telemetry.events import InstanceStarted


setup_logging()
_logger = logging.getLogger(__name__)


def _app_version() -> str:
    try:
        from importlib.metadata import version
        return version("cognitor")
    except Exception:
        return "unknown"


async def _warm_models(
    registry: EmbedderRegistry,
    qa_extractor: ExtractiveQA,
    reranker: Reranker,
    model_names: list[str],
    event: asyncio.Event,
) -> None:
    for model_name in model_names:
        try:
            await run_sync(lambda m=model_name: registry.get(m))
            _logger.info("Warmed up embedder: %s", model_name)
        except Exception:
            _logger.exception("Failed to warm up embedder: %s", model_name)

    try:
        await run_sync(qa_extractor.warmup)
        _logger.info("Warmed up extractive QA model: %s", qa_extractor.model_name)
    except Exception:
        _logger.exception("Failed to warm up extractive QA model: %s", qa_extractor.model_name)

    try:
        await run_sync(reranker.warmup)
        _logger.info("Warmed up reranker model: %s", reranker.model_name)
    except Exception:
        _logger.exception("Failed to warm up reranker model: %s", reranker.model_name)

    event.set()
    _logger.info("All models ready")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Cognitor is starting up")
    config = get_config()

    from src.embeddings.providers.sentence_transformers import register_sentence_transformers
    embedder_registry = EmbedderRegistry()
    for model_name in config.emb_models:
        register_sentence_transformers(embedder_registry, model_name)
        _logger.info("Registered sentence-transformers embedder: %s", model_name)

    qa_extractor = ExtractiveQA(
        model_name=config.qa_model,
        min_score=config.qa_min_score,
    )

    reranker = Reranker(model_name=config.rerank_model)

    models_ready = asyncio.Event()
    database = Database()
    authenticator = build_authenticator(config)

    telemetry_client = TelemetryClient(
        instance_id=resolve_instance_id(config.telemetry_instance_id),
        endpoint=config.telemetry_endpoint if config.telemetry_enabled else "",
        api_key=config.telemetry_api_key,
    )

    app.state.app_state = AppState(
        config=config,
        database=database,
        compaction_scheduler=CompactionScheduler(
            threshold=config.compaction_threshold,
        ),
        embedder_registry=embedder_registry,
        qa_extractor=qa_extractor,
        reranker=reranker,
        models_ready=models_ready,
        telemetry_client=telemetry_client,
        authenticator=authenticator,
    )

    await telemetry_client.start()
    telemetry_client.enqueue(
        InstanceStarted(
            version=_app_version(),
            emb_model_count=len(config.emb_models),
            collection_count=len(database.list_collections()),
        )
    )

    asyncio.create_task(
        _warm_models(
            embedder_registry,
            qa_extractor,
            reranker,
            config.emb_models,
            models_ready,
        )
    )
    yield
    _logger.info("Cognitor is shutting down")
    if authenticator is not None:
        await authenticator.aclose()
    await telemetry_client.stop()
    
app = FastAPI(
    title="Cognitor REST API",
    lifespan=lifespan
)

# ----- Middleware -----

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.add_middleware(AuthMiddleware)

# ----- Exception handlers -----

# Handler for ValueError.
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code = status.HTTP_400_BAD_REQUEST,
        content = ErrorResponse(
            message=str(exc) or "Invalid request data"
        ).model_dump()
    )
    
# Handler for fastapi ValidationException and RequestValidationError.
@app.exception_handler(ValidationException)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: ValidationException):
    validation_errors: list[dict[str, Optional[str]]] = []

    for error in exc.errors():
        validation_errors.append({
            "location": ".".join([str(err) for err in error["loc"]]),
            "message": error.get("msg", None),
            "input_data": error.get("input", None),
        })

    return JSONResponse(
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
        content = ErrorResponse(
            message="Validation failed",
            details={ "validation_errors": validation_errors }
        ).model_dump()
    )
    
# Handler for fastapi HTTPException.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code = exc.status_code,
        content = ErrorResponse(
            message=str(exc.detail)
        ).model_dump()
    )
    
# Handlers for domain exceptions.
@app.exception_handler(CollectionNotFoundError)
@app.exception_handler(DocumentNotFoundError)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(message=str(exc)).model_dump()
    )

@app.exception_handler(CollectionAlreadyExistsError)
async def conflict_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(message=str(exc)).model_dump()
    )

@app.exception_handler(InvalidCollectionNameError)
@app.exception_handler(InvalidDimensionError)
@app.exception_handler(InvalidDocumentInputError)
@app.exception_handler(DimensionMismatchError)
async def domain_bad_request_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(message=str(exc)).model_dump()
    )

@app.exception_handler(EmbedderNotFoundError)
async def embedder_not_found_handler(request: Request, exc: EmbedderNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(message=str(exc)).model_dump()
    )

@app.exception_handler(EmbeddingError)
async def embedding_error_handler(request: Request, exc: EmbeddingError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(message=str(exc)).model_dump()
    )

# Catch-all handler for unhandled exceptions.
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    _logger.error(
        f"Unhandled exception on {request.method} {request.url.path}:\n"
        f"{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}"
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="Internal server error"
        ).model_dump()
    )

# ----- Endpoints -----

app.include_router(
    prefix="",
    router=base_router,
    tags=["base endpoints"]
)

app.include_router(
    prefix="/collections",
    router=collections_router,
    tags=["collection management"]
)

app.include_router(
    prefix="/admin",
    router=admin_router,
    tags=["admin endpoints"]
)


def _custom_openapi():
    # This custom OpenAPI function is needed to add the security scheme for API key 
    # authentication, which ensures that the Swagger UI will show an "Authorize" button
    # at the top right. 
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    schema.setdefault("components", {})["securitySchemes"] = {
        "ApiKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "Enter your API key in the X-API-Key header",
        },
    }
    schema["security"] = [{"ApiKeyHeader": []}]
    app.openapi_schema = schema
    return schema


app.openapi = _custom_openapi