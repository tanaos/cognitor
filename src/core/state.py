import asyncio
from dataclasses import dataclass

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry


@dataclass
class AppState:
    config: Config
    database: Database
    compaction_scheduler: CompactionScheduler
    embedder_registry: EmbedderRegistry
    models_ready: asyncio.Event
