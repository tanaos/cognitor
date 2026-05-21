from dataclasses import dataclass

from src.config.settings import Config
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler


@dataclass
class AppState:
    config: Config
    database: Database
    compaction_scheduler: CompactionScheduler
