from typing import Any

from src.core.models import SearchResult


class Reranker:
    """
    Multilingual cross-encoder reranker.

    Uses a cross-encoder model to re-score query-passage pairs, which is more
    accurate than the bi-encoder similarity used during retrieval.

    Default model: ``BAAI/bge-reranker-v2-m3`` — a multilingual reranker
    supporting 100+ languages, suitable for cross-lingual retrieval scenarios.
    """

    def __init__(self, model_name: str) -> None:
        self._model_name = model_name
        self._model: Any = None

    @property
    def model_name(self) -> str:
        return self._model_name

    def warmup(self) -> None:
        """
        Load the model into memory so the first search request is not penalised.
        """
        
        self._load()

    def _load(self) -> None:
        if self._model is not None:
            return
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(self._model_name)

    def rerank(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """
        Rerank search results using the cross-encoder model.

        Args:
            query: The original query text.
            results: List of SearchResult objects to rerank.

        Returns:
            A new list of SearchResult objects sorted by descending relevance
            score, with scores replaced by the cross-encoder logits.
        """
        if not results:
            return results

        self._load()

        pairs = [(query, result.text) for result in results]
        scores = self._model.predict(pairs)

        reranked = [
            SearchResult(
                id=r.id,
                score=float(score),
                text=r.text,
                metadata=r.metadata,
                vector=r.vector,
            )
            for r, score in zip(results, scores)
        ]
        reranked.sort(key=lambda r: r.score, reverse=True)
        return reranked
