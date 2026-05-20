import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from src.storage.compaction import CompactionResult

if TYPE_CHECKING:
    from src.core.database import Database


_logger = logging.getLogger(__name__)


class CompactionScheduler:
    """
    Monitors soft-deletion ratios per collection and triggers background
    compaction when the ratio exceeds a configurable threshold.

    A single ``asyncio.Lock`` per collection serialises both compaction jobs
    and normal write operations (add / delete), preventing races between a
    concurrent write and an in-progress compaction that is rewriting the
    vector file and metadata store.
    """

    def __init__(self, threshold: float, database: "Database") -> None:
        """
        Args:
            threshold: Fraction of soft-deleted vectors (0-1) above which
                automatic compaction is triggered.
            database: The ``Database`` instance used to open collection storage.
        """
        self._threshold = threshold
        self._database = database
        self._locks: dict[str, asyncio.Lock] = {}
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="compaction"
        )

    def get_collection_lock(self, name: str) -> asyncio.Lock:
        """
        Return the per-collection asyncio lock, creating it if necessary.
        
        Args:
            name: Collection name
            
        Returns:
            The asyncio.Lock instance for this collection.
        """
        if name not in self._locks:
            self._locks[name] = asyncio.Lock()
        return self._locks[name]

    async def check_and_schedule(self, collection_name: str) -> None:
        """
        Check the deletion ratio for a collection and schedule a background
        compaction task if the threshold is exceeded and no compaction is
        already running.

        This method is non-blocking and returns immediately; the compaction
        itself runs as a background asyncio task.

        Args:
            collection_name: Name of the collection to inspect.
        """
        lock = self.get_collection_lock(collection_name)
        if lock.locked():
            return  # compaction already in progress

        try:
            storage = self._database.get_collection_ref(collection_name)
        except KeyError:
            return

        total = storage.vectors.load_size()
        if total == 0:
            return

        live = storage.metadata.count()
        deleted = total - live
        ratio = deleted / total

        if ratio >= self._threshold:
            _logger.info(
                "Collection '%s': deletion ratio %.1f%% >= threshold %.1f%%, "
                "scheduling compaction",
                collection_name,
                ratio * 100,
                self._threshold * 100,
            )
            asyncio.create_task(self._run_compaction(collection_name))

    async def compact_now(self, collection_name: str) -> CompactionResult:
        """
        Force immediate compaction of a collection, blocking until done.

        Args:
            collection_name: Name of the collection to compact.

        Returns:
            A ``CompactionResult`` describing the outcome.
        """
        from src.storage.compaction import compact

        lock = self.get_collection_lock(collection_name)
        if lock.locked():
            raise RuntimeError(
                f"Compaction is already running for collection '{collection_name}'"
            )

        async with lock:
            loop = asyncio.get_running_loop()
            storage = self._database.get_collection_ref(collection_name)
            return await loop.run_in_executor(
                self._executor,
                lambda: compact(collection_name, storage),
            )

    async def _run_compaction(self, collection_name: str) -> None:
        from src.storage.compaction import compact

        lock = self.get_collection_lock(collection_name)
        async with lock:
            _logger.info("Compaction started for collection '%s'", collection_name)
            try:
                loop = asyncio.get_running_loop()
                storage = self._database.get_collection_ref(collection_name)
                result = await loop.run_in_executor(
                    self._executor,
                    lambda: compact(collection_name, storage),
                )
                _logger.info(
                    "Compaction complete for '%s': %d deleted vectors removed, "
                    "%d remaining",
                    collection_name,
                    result.deleted_count,
                    result.live_count,
                )
            except Exception:
                _logger.exception(
                    "Compaction failed for collection '%s'", collection_name
                )
