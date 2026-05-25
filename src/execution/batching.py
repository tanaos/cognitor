from typing import Optional

from src.core.collection import Collection
from src.core.types import Vector, Metadata, DocumentId
from src.embeddings.base import Embedder

DEFAULT_BATCH_SIZE = 512


def batch_add_documents(
    collection: Collection,
    texts: list[str],
    metadatas: list[Metadata],
    vectors: Optional[list[Vector]] = None,
    embedder: Optional[Embedder] = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[DocumentId]:
    """
    Add a large list of documents to a collection in fixed-size batches.

    When *embedder* is supplied and *vectors* is ``None``, each batch is
    embedded independently so that memory pressure stays bounded regardless
    of the total input size.

    Args:
        collection: Target collection service instance.
        texts: Full list of document texts.
        metadatas: Full list of metadata dicts (must be same length as texts).
        vectors: Pre-computed vectors. If provided, *embedder* is ignored.
        embedder: Embedder used to produce vectors when *vectors* is ``None``.
        batch_size: Number of documents processed per batch.

    Returns:
        Flat list of assigned document IDs in insertion order.
    """
    if vectors is None and embedder is None:
        raise ValueError("either vectors or embedder must be provided")

    ids: list[DocumentId] = []

    for start in range(0, len(texts), batch_size):
        end = start + batch_size
        batch_texts = texts[start:end]
        batch_metadatas = metadatas[start:end]

        if vectors is not None:
            batch_vectors: list[Vector] = vectors[start:end]
        else:
            if embedder is None:
                raise ValueError("embedder must be provided when vectors is None")
            batch_vectors = embedder.embed(batch_texts).tolist()

        batch_ids = collection.add_documents(
            vectors=batch_vectors,
            texts=batch_texts,
            metadatas=batch_metadatas,
        )
        ids.extend(batch_ids)

    return ids
