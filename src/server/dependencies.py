import asyncio
from typing import Optional
from fastapi import Request, HTTPException, status

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.search.extractive_qa import ExtractiveQA
from src.search.rerank import Reranker
from src.server.auth.service import AuthenticatedUser
from src.telemetry.client import TelemetryClient
from src.storage.users import UserStore


def get_config(request: Request) -> Config:
    return request.app.state.app_state.config


def get_database(request: Request) -> Database:
    """
    Return a Database scoped to the current user when multi_tenant is enabled,
    otherwise return the global Database instance.
    """
    config = request.app.state.app_state.config
    if config.multi_tenant:
        user = _require_current_user(request)
        return Database(root_path=f"storage/collections/{user.id}")
    return request.app.state.app_state.database


def get_scheduler(request: Request) -> CompactionScheduler:
    return request.app.state.app_state.compaction_scheduler


def get_embedder_registry(request: Request) -> EmbedderRegistry:
    return request.app.state.app_state.embedder_registry


def get_qa_extractor(request: Request) -> ExtractiveQA:
    return request.app.state.app_state.qa_extractor


def get_reranker(request: Request) -> Reranker:
    return request.app.state.app_state.reranker


def get_models_ready(request: Request) -> asyncio.Event:
    return request.app.state.app_state.models_ready


def get_telemetry_client(request: Request) -> TelemetryClient:
    return request.app.state.app_state.telemetry_client


def get_user_store(request: Request) -> Optional[UserStore]:
    return request.app.state.app_state.user_store


def get_current_user(request: Request) -> Optional[AuthenticatedUser]:
    """Return the authenticated user, or None when multi_tenant is disabled."""
    return getattr(request.state, "current_user", None)


def _require_current_user(request: Request) -> AuthenticatedUser:
    """Return the authenticated user, raising 401 if not present."""
    user = getattr(request.state, "current_user", None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


def collection_lock_key(request: Request, collection_name: str) -> str:
    """
    Build the per-collection lock key, namespaced by user in multi-tenant mode.
    """
    config = request.app.state.app_state.config
    if config.multi_tenant:
        user = _require_current_user(request)
        return f"{user.id}:{collection_name}"
    return collection_name

