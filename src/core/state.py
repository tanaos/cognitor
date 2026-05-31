import asyncio
from typing import TYPE_CHECKING, Optional

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.search.extractive_qa import ExtractiveQA
from src.telemetry.client import TelemetryClient

if TYPE_CHECKING:
    from src.storage.users import UserStore


class AppState:
    def __init__(
        self,
        config: Config,
        database: Database,
        compaction_scheduler: CompactionScheduler,
        embedder_registry: EmbedderRegistry,
        qa_extractor: ExtractiveQA,
        models_ready: asyncio.Event,
        telemetry_client: TelemetryClient,
        user_store: Optional["UserStore"] = None,
    ) -> None:
        self.config = config
        self.database = database
        self.compaction_scheduler = compaction_scheduler
        self.embedder_registry = embedder_registry
        self.qa_extractor = qa_extractor
        self.models_ready = models_ready
        self.telemetry_client = telemetry_client
        self.user_store = user_store

