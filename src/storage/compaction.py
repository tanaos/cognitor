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

    Collects every live document via the metadata store, writes a new dense
    vector file via an atomic rename, then updates ``vector_pos`` for each
    surviving document in a single SQLite transaction. Document UUIDs are
    never changed. Finally the WAL is compacted.

    Args:
        name: Collection name (used only for the result object).
        storage: The ``CollectionStorage`` instance to compact.

    Returns:
        A ``CompactionResult`` describing what was removed.
    """
    total = storage.vectors.load_size()
    live_docs = storage.metadata.list_all_live()
    live_count = len(live_docs)
    deleted_count = total - live_count

    if deleted_count == 0:
        return CompactionResult(
            collection_name=name,
            vectors_before=total,
            live_count=live_count,
            deleted_count=0,
        )

    live_vectors: list[np.ndarray] = []
    if live_count > 0:
        storage.vectors.open("r")
        assert storage.vectors.vectors is not None
        for _doc_id, vector_pos, _meta in live_docs:
            live_vectors.append(storage.vectors.vectors[vector_pos].copy())

    new_vectors: np.ndarray = (
        np.stack(live_vectors).astype(storage.vectors.dtype)
        if live_count > 0
        else np.empty((0, storage.vectors.dim), dtype=storage.vectors.dtype)
    )

    # Build updated live_docs with new sequential vector positions (0, 1, 2, …).
    updated_live_docs = [
        (doc_id, new_pos, meta)
        for new_pos, (doc_id, _old_pos, meta) in enumerate(live_docs)
    ]

    # Atomically replace the vector file then rewrite metadata with new vector_pos values.
    # Document UUIDs are preserved.
    storage.vectors.replace_all(new_vectors)
    storage.metadata.rewrite(updated_live_docs)

    # Compact the WAL to remove any pending entries that are now obsolete after the rewrite,
    # so that it doesn't grow indefinitely.
    storage.wal.compact()

    return CompactionResult(
        collection_name=name,
        vectors_before=total,
        live_count=live_count,
        deleted_count=deleted_count,
    )
