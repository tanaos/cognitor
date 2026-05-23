from typing import Callable

from src.embeddings.base import Embedder
from src.embeddings.exceptions import EmbedderNotFoundError


class EmbedderRegistry:
    """
    Registry that maps model IDs to embedder factories.

    Factories are called at most once per model ID; the resulting
    :class:`~src.embeddings.base.Embedder` instance is cached for the
    lifetime of the registry.
    """

    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], Embedder]] = {}
        self._cache: dict[str, Embedder] = {}

    def register(self, model_id: str, factory: Callable[[], Embedder]) -> None:
        """
        Register a factory for *model_id*, replacing any previous entry.

        Args:
            model_id: Identifier that matches a collection's ``emb_model`` field.
            factory: Zero-argument callable returning an :class:`Embedder` instance.
        """
        self._factories[model_id] = factory
        self._cache.pop(model_id, None)

    def get(self, model_id: str) -> Embedder:
        """
        Return the cached :class:`Embedder` for *model_id*, creating it on first access.

        Args:
            model_id: Identifier of the desired embedder.
        Returns:
            The cached :class:`Embedder` instance for *model_id*.
        """
        if model_id not in self._factories:
            raise EmbedderNotFoundError(model_id)
        if model_id not in self._cache:
            self._cache[model_id] = self._factories[model_id]()
        return self._cache[model_id]

    def list_registered(self) -> list[str]:
        """
        Return the sorted list of registered model IDs.
        
        Returns:
            Sorted list of registered model IDs.
        """
        return sorted(self._factories.keys())
