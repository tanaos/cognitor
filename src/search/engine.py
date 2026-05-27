import numpy as np
from typing import Optional

from src.indexes.faiss_hnsw import FaissHNSWIndex
from src.storage.metadata import MetadataStore
from src.storage.vectors import VectorStore
from src.core.models import SearchResult
from src.core.types import Vector
from src.search.filters import FilterSpec, apply as apply_filters


_OVERSAMPLE_FACTOR = 3


# TODO: reassess filtering logic with oversampling
# TODO: users should be able to decide which search steps shoud be performed and which shouldn't;
# in particular, the q&a step only add meaningful information if the user query is a question,
# but it would be a waste of resources for keyword search queries.
class SearchEngine:
    """
    Executes vector similarity searches with optional metadata search or filtering.
    """

    def __init__(
        self,
        index: FaissHNSWIndex,
        metadata_store: MetadataStore,
        vector_store: VectorStore,
    ) -> None:
        self._index = index
        self._metadata_store = metadata_store
        self._vector_store = vector_store

    def search(
        self,
        query_vector: Vector,
        top_k: int,
        filters: Optional[FilterSpec] = None,
        include_vectors: bool = False,
    ) -> list[SearchResult]:
        """
        Search for the most similar documents to a query vector, optionally applying metadata 
        filters.
        
        Args:
            query_vector: Query vector with the same dimensionality as the collection.
            top_k: Maximum number of results to return.
            filters: Optional metadata equality filters, e.g. {"genre": "sci-fi"}.
            include_vectors: Whether to include raw vectors in the results.
            
        Returns:
            List of SearchResult objects ordered by descending similarity score.
        """
        
        if self._index.ntotal == 0:
            return []

        # Oversample when filtering so we still have top_k results after elimination.
        fetch_k = min(
            top_k * _OVERSAMPLE_FACTOR if filters else top_k,
            self._index.ntotal,
        )

        query_arr = np.array(query_vector, dtype=np.float32)
        scores, positions = self._index.search(query_arr, fetch_k)

        valid = [
            (int(pos), float(score))
            for pos, score in zip(positions, scores)
            if pos != -1
        ]
        if not valid:
            return []

        valid_positions = [pos for pos, _ in valid]
        score_map = {pos: score for pos, score in valid}

        docs = self._metadata_store.get_by_vector_positions(valid_positions)

        if include_vectors:
            self._vector_store.open("r")

        results: list[SearchResult] = []
        for doc in docs:
            vector = None
            if include_vectors and self._vector_store.vectors is not None:
                vector = self._vector_store.vectors[doc.vector_pos].tolist()
            results.append(
                SearchResult(
                    id=doc.id,
                    score=score_map[doc.vector_pos],
                    text=doc.text,
                    metadata=doc.metadata,
                    vector=vector,
                )
            )

        results = apply_filters(results, filters)
        results.sort(key=lambda r: r.score)  # L2 distance: lower = more similar
        return results[:top_k]
