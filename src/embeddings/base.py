from abc import ABC, abstractmethod

import numpy as np


class Embedder(ABC):
    """Abstract base class for text embedders."""

    @property
    @abstractmethod
    def dim(self) -> int:
        """Dimensionality of the produced embeddings."""
        ...

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Embed a list of texts into vectors.

        Args:
            texts: List of strings to embed.

        Returns:
            np.ndarray of shape (len(texts), dim).
        """
        ...
