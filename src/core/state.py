import asyncio
from typing import Optional

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.embeddings.registry import EmbedderRegistry
from src.search.extractive_qa import ExtractiveQA
from src.search.rerank import Reranker
from src.server.auth.service import Authenticator
from src.telemetry.client import TelemetryClient


class AppState:
    def __init__(
        self,
        config: Config,
        database: Database,
        compaction_scheduler: CompactionScheduler,
        embedder_registry: EmbedderRegistry,
        qa_extractor: ExtractiveQA,
        reranker: Reranker,
        models_ready: asyncio.Event,
        telemetry_client: TelemetryClient,
        authenticator: Optional[Authenticator] = None,
    ) -> None:
        self.config = config
        self.database = database
        self.compaction_scheduler = compaction_scheduler
        self.embedder_registry = embedder_registry
        self.qa_extractor = qa_extractor
        self.reranker = reranker
        self.models_ready = models_ready
        self.telemetry_client = telemetry_client
        self.authenticator = authenticator

