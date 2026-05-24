import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ValidationException
import traceback

from .base.routers import base_router
from .collections.routers import collections_router
from .admin.routers import admin_router
from .responses import ErrorResponse
from .middleware.auth import AuthMiddleware

from src.utils.logging import setup_logging
from src.config.settings import get_config
from src.storage.orm import init_db
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


setup_logging()
_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("Cognitor is starting up")
    config = get_config()

    from src.embeddings.providers.sentence_transformers import register_sentence_transformers
    embedder_registry = EmbedderRegistry()
    for model_name in config.emb_models:
        register_sentence_transformers(embedder_registry, model_name)
        _logger.info("Registered sentence-transformers embedder: %s", model_name)

    default_model = config.default_emb_model
    if default_model and embedder_registry.list_registered():
        _logger.info("Loading default embedder: %s", default_model)
        embedder_registry.get(default_model)

    database = Database()
    app.state.app_state = AppState(
        config=config,
        database=database,
        compaction_scheduler=CompactionScheduler(
            threshold=config.compaction_threshold,
            database=database,
        ),
        embedder_registry=embedder_registry,
    )
    init_db()
    yield
    _logger.info("Cognitor is shutting down")
    
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