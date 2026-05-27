import asyncio
from fastapi import Request

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.search.extractive_qa import ExtractiveQA


def get_config(request: Request) -> Config:
    return request.app.state.app_state.config


def get_database(request: Request) -> Database:
    return request.app.state.app_state.database


def get_scheduler(request: Request) -> CompactionScheduler:
    return request.app.state.app_state.compaction_scheduler


def get_embedder_registry(request: Request) -> EmbedderRegistry:
    return request.app.state.app_state.embedder_registry


def get_qa_extractor(request: Request) -> ExtractiveQA:
    return request.app.state.app_state.qa_extractor


def get_models_ready(request: Request) -> asyncio.Event:
    return request.app.state.app_state.models_ready
