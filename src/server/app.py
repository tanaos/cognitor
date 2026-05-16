import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, ValidationException
import traceback

from .base.routers import base_router
from .responses import ErrorResponse

from src.utils.logging import setup_logging
from src.config.settings import get_config
from src.core.database import init_db


setup_logging()
_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _logger.info("cognitor is starting up")
    app.state.config = get_config()
    init_db()
    yield
    _logger.info("cognitor is shutting down")
    
app = FastAPI(
    title="Cognitor REST API",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ----- Exception handlers -----

# Handler for ValueError.
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code = status.HTTP_400_BAD_REQUEST,
        content = "The provided data is invalid or corrupted."
    )
    
# Handler for fastapi ValidationException and RequestValidationError.
@app.exception_handler(ValidationException)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: ValidationException):
    validation_errors: list[dict[str, str | None]] = []

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