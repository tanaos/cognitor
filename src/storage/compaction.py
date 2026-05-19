from dataclasses import dataclass

import numpy as np

from src.storage.collection import CollectionStorage


@dataclass
class CompactionResult:
    collection_name: str
    vectors_before: int
    live_count: int
    deleted_count: int


def compact(name: str, storage: CollectionStorage) -> CompactionResult:
    """
    Rewrite the collection removing all soft-deleted vectors.

    Collects every live document, writes a new dense vector file via an atomic
    rename, then rewrites the metadata store with new sequential IDs (0 …
    live_count-1) in a single SQLite transaction.  Finally the WAL is
    compacted.

    This operation reassigns document IDs.  Any external references to the
    old IDs will be invalid after compaction completes.

    Args:
        name: Collection name (used only for the result object).
        storage: The ``CollectionStorage`` instance to compact.

    Returns:
        A ``CompactionResult`` describing what was removed.
    """
    total = storage.id_counter

    live_vectors: list[np.ndarray] = []
    live_metadatas: list[dict[str, str]] = []

    if total > 0:
        storage.vectors.open("r")
        assert storage.vectors.vectors is not None

        for doc_id in range(total):
            meta = storage.metadata.get(doc_id)
            if meta is None:
                continue
            live_vectors.append(storage.vectors.vectors[doc_id].copy())
            live_metadatas.append(meta)

    live_count = len(live_vectors)
    deleted_count = total - live_count

    if deleted_count == 0:
        return CompactionResult(
            collection_name=name,
            vectors_before=total,
            live_count=live_count,
            deleted_count=0,
        )

    new_vectors: np.ndarray = (
        np.stack(live_vectors).astype(storage.vectors.dtype)
        if live_count > 0
        else np.empty((0, storage.vectors.dim), dtype=storage.vectors.dtype)
    )

    # Atomically replace the vector file then rewrite metadata.
    storage.vectors.replace_all(new_vectors)
    storage.metadata.rewrite(list(range(live_count)), live_metadatas)

    storage.id_counter = live_count
    # Compact the WAL to remove any pending entries that are now obsolete after the rewrite,
    # so that it doesn't grow indefinitely.
    storage.wal.compact()

    return CompactionResult(
        collection_name=name,
        vectors_before=total,
        live_count=live_count,
        deleted_count=deleted_count,
    )
