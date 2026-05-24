from fastapi import Request

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry


def get_config(request: Request) -> Config:
    return request.app.state.app_state.config


def get_database(request: Request) -> Database:
    return request.app.state.app_state.database


def get_scheduler(request: Request) -> CompactionScheduler:
    return request.app.state.app_state.compaction_scheduler


def get_embedder_registry(request: Request) -> EmbedderRegistry:
    return request.app.state.app_state.embedder_registry
