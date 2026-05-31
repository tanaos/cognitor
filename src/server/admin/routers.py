from typing import Annotated
import time

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from src.server.dependencies import get_scheduler, get_telemetry_client, get_database
from src.core.database import Database
from src.execution.scheduler import CompactionScheduler
from src.telemetry.client import TelemetryClient
from src.telemetry.events import CompactionRun

DatabaseDep = Annotated[Database, Depends(get_database)]
SchedulerDep = Annotated[CompactionScheduler, Depends(get_scheduler)]
TelemetryDep = Annotated[TelemetryClient, Depends(get_telemetry_client)]


admin_router = APIRouter()


class CompactionResponse(BaseModel):
    collection_name: str
    vectors_before: int
    live_count: int
    deleted_count: int


@admin_router.post(
    path="/collections/{name}/compact",
    responses={
        status.HTTP_200_OK: {
            "description": "Compaction completed successfully",
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Collection not found",
        },
        status.HTTP_409_CONFLICT: {
            "description": "Compaction already running for this collection",
        },
    },
)
async def compact_collection(
    name: str, database: DatabaseDep, scheduler: SchedulerDep, telemetry: TelemetryDep
) -> CompactionResponse:
    """
    Compact a collection by physically removing all soft-deleted vectors and
    reassigning document IDs.  Blocks until compaction is complete.

    This endpoint is intended for manual operator use.  Automatic threshold-
    based compaction is handled by the background scheduler.
    """
    t0 = time.monotonic()
    try:
        result = await scheduler.compact_now(name, database)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Collection '{name}' does not exist",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.args[0],
        )
    telemetry.enqueue(CompactionRun(
        vectors_before=result.vectors_before,
        live_count=result.live_count,
        deleted_count=result.deleted_count,
        duration_ms=(time.monotonic() - t0) * 1000,
    ))
    return CompactionResponse(
        collection_name=result.collection_name,
        vectors_before=result.vectors_before,
        live_count=result.live_count,
        deleted_count=result.deleted_count,
    )
