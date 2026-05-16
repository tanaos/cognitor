import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .base.routers import base_router

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

# ----- Endpoints -----

app.include_router(
    prefix="",
    router=base_router,
    tags=["base endpoints"]
)