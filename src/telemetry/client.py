import asyncio
import dataclasses
import logging
import re
import uuid
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from .events import TelemetryEvent


_CAMEL_TO_SNAKE_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _event_name(event: TelemetryEvent) -> str:
    return _CAMEL_TO_SNAKE_RE.sub("_", type(event).__name__).lower()


def resolve_instance_id(configured_id: str, storage_dir: Path = Path("storage")) -> str:
    """
    Return the configured instance ID, or read/create a persistent one on disk.
    
    Args:
        configured_id: The instance ID from the config.  If non-empty, this is returned directly.
        storage_dir: Directory where the instance ID file is stored if no configured ID is provided.
    Returns:
        A string instance ID that is stable across restarts.
    """
    
    if configured_id:
        return configured_id
    id_file = storage_dir / "instance_id"
    if id_file.exists():
        return id_file.read_text().strip()
    new_id = str(uuid.uuid4())
    storage_dir.mkdir(parents=True, exist_ok=True)
    id_file.write_text(new_id)
    return new_id


class TelemetryClient:
    """
    Collects telemetry events and flushes them in batches to a remote ingestion
    endpoint. All operations are non-blocking for the caller; the flush runs
    in a background asyncio task.

    When ``endpoint`` is empty the client operates in no-op mode: ``enqueue``
    returns immediately and no network connections are made.
    """

    def __init__(
        self,
        instance_id: str,
        endpoint: str,
        api_key: str,
        flush_interval: float = 60.0,
        max_batch_size: int = 50,
    ) -> None:
        self._enabled = bool(endpoint)
        self._instance_id = instance_id
        self._endpoint = endpoint
        self._api_key = api_key
        self._flush_interval = flush_interval
        self._max_batch_size = max_batch_size
        self._queue: deque[dict[str, Any]] = deque()
        self._flush_event = asyncio.Event()
        self._task: asyncio.Task | None = None
        self._http: httpx.AsyncClient | None = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enqueue(self, event: TelemetryEvent) -> None:
        """
        Queue an event for the next flush.
        
        Args:
            event: A dataclass instance representing the telemetry event to be sent.
        """
        
        if not self._enabled:
            return
        payload = dataclasses.asdict(event)
        payload["event"] = _event_name(event)
        payload["instance_id"] = self._instance_id
        payload["ts"] = datetime.now(timezone.utc).isoformat()
        self._queue.append(payload)
        if len(self._queue) >= self._max_batch_size:
            self._flush_event.set()

    async def start(self) -> None:
        """
        Start the background flush task. Call once during app startup.
        """
        
        if not self._enabled:
            return
        self._http = httpx.AsyncClient(timeout=10.0)
        self._task = asyncio.create_task(self._flush_loop(), name="telemetry_flush")

    async def stop(self) -> None:
        """
        Cancel the flush task and drain any remaining queued events.
        """
        
        if not self._enabled:
            return
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._flush_once()
        if self._http is not None:
            await self._http.aclose()

    async def _flush_loop(self) -> None:
        """
        Background task that waits for flush events or a timeout, then flushes the queue.
        """
        
        while True:
            try:
                await asyncio.wait_for(
                    self._flush_event.wait(), timeout=self._flush_interval
                )
            except asyncio.TimeoutError:
                pass
            self._flush_event.clear()
            await self._flush_once()

    async def _flush_once(self) -> None:
        """
        Flush the queued events once. This method is called by the background
        flush loop or during shutdown to ensure all events are sent.
        """
        
        if not self._queue or self._http is None:
            return
        batch: list[dict[str, Any]] = []
        while self._queue and len(batch) < self._max_batch_size:
            batch.append(self._queue.popleft())
        try:
            response = await self._http.post(
                self._endpoint,
                json={"events": batch},
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            response.raise_for_status()
        except Exception:
            pass
