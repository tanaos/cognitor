import numpy as np

from src.embeddings.base import Embedder
from src.embeddings.exceptions import EmbeddingError
from src.embeddings.registry import EmbedderRegistry


class SentenceTransformersEmbedder(Embedder):
    """
    Embedder backed by a `sentence-transformers` model.

    The underlying model is loaded lazily on first use and cached for the
    lifetime of the process.

    Args:
        model_name: Any model name accepted by ``SentenceTransformer()``,
            e.g. ``"all-MiniLM-L6-v2"`` or a local path.
    """

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import]
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers is not installed. "
                "Install it with: pip install sentence-transformers"
            ) from exc

        self._model_name = model_name
        self._model = SentenceTransformer(model_name)

    @property
    def dim(self) -> int:
        return self._model.get_sentence_embedding_dimension()  # type: ignore[return-value]

    def embed(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(texts, convert_to_numpy=True)  # type: ignore[return-value]


def register_sentence_transformers(registry: EmbedderRegistry, model_name: str) -> None:
    """
    Convenience helper that registers a :class:`SentenceTransformersEmbedder`
    for *model_name* in *registry*.

    Call this once at application startup for each sentence-transformers model
    you want to use for automatic embedding.

    Example::

        from src.embeddings.registry import EmbedderRegistry
        from src.embeddings.providers.sentence_transformers import register_sentence_transformers

        registry = EmbedderRegistry()
        register_sentence_transformers(registry, "all-MiniLM-L6-v2")

    Args:
        registry: The :class:`~src.embeddings.registry.EmbedderRegistry` to register into.
        model_name: Model name passed to ``SentenceTransformer()``. This string
            is also used as the registry key and must match the ``emb_model``
            field of any collection that should use this embedder.
    """
    registry.register(model_name, lambda: SentenceTransformersEmbedder(model_name))
