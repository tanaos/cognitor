from typing import Optional

from anyio.to_thread import run_sync

from src.core.collection import Collection
from src.core.types import DocumentId, Metadata, Vector
from src.embeddings.base import Embedder
from src.execution.scheduler import CompactionScheduler


async def bulk_ingest(
    *,
    collection: Collection,
    lock_key: str,
    scheduler: CompactionScheduler,
    texts: list[str],
    metadatas: list[Metadata],
    vectors: Optional[list[Vector]] = None,
    embedder: Optional[Embedder] = None,
    batch_size: int = 512,
) -> list[DocumentId]:
    """
    Ingest a large list of documents in fixed-size batches, acquiring the
    per-collection lock only for each individual storage write.

    Embedding (when *embedder* is provided) runs outside the lock because it
    is CPU-bound and does not touch shared storage.  The lock is released
    between batches so concurrent read requests can interleave.

    Args:
        collection: Target collection service instance.
        lock_key: Unique string key used by *scheduler* to look up the lock.
        scheduler: CompactionScheduler that owns the per-collection locks.
        texts: Full list of document texts.
        metadatas: Full list of metadata dicts (same length as *texts*).
        vectors: Pre-computed vectors. When provided *embedder* is ignored.
        embedder: Embedder used to produce vectors when *vectors* is ``None``.
        batch_size: Number of documents processed per storage transaction.

    Returns:
        Flat list of assigned document IDs in insertion order.
    """
    if vectors is None and embedder is None:
        raise ValueError("either vectors or embedder must be provided")

    document_ids: list[DocumentId] = []
    n = len(texts)

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch_texts = texts[start:end]
        batch_metas = metadatas[start:end]

        if vectors is not None:
            batch_vectors: list[Vector] = vectors[start:end]
        else:
            assert embedder is not None
            # Embed outside the lock — CPU-bound, does not touch shared storage.
            batch_arr = await run_sync(embedder.embed, batch_texts)
            batch_vectors = batch_arr.tolist()

        async with scheduler.get_collection_lock(lock_key):
            batch_ids = await run_sync(
                collection.add_documents,
                batch_vectors,
                batch_texts,
                batch_metas,
            )
        document_ids.extend(batch_ids)

    return document_ids
