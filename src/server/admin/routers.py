from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from src.server.dependencies import get_scheduler
from src.execution.scheduler import CompactionScheduler

SchedulerDep = Annotated[CompactionScheduler, Depends(get_scheduler)]


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
async def compact_collection(name: str, scheduler: SchedulerDep) -> CompactionResponse:
    """
    Compact a collection by physically removing all soft-deleted vectors and
    reassigning document IDs.  Blocks until compaction is complete.

    This endpoint is intended for manual operator use.  Automatic threshold-
    based compaction is handled by the background scheduler.
    """
    try:
        result = await scheduler.compact_now(name)
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
    return CompactionResponse(
        collection_name=result.collection_name,
        vectors_before=result.vectors_before,
        live_count=result.live_count,
        deleted_count=result.deleted_count,
    )
