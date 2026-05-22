from abc import ABC, abstractmethod

import numpy as np


class VectorIndex(ABC):

    @abstractmethod
    def add(self, positions: np.ndarray, vectors: np.ndarray) -> None:
        """Add vectors with their corresponding vector_pos IDs."""
        ...

    @abstractmethod
    def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        """Return (scores, positions) arrays of length top_k."""
        ...

    @abstractmethod
    def rebuild(self, positions: np.ndarray, vectors: np.ndarray) -> None:
        """Discard the current index and rebuild from scratch."""
        ...

    @abstractmethod
    def save(self, path: str) -> None:
        """Persist the index to the given collection directory."""
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        """Load the index from the given collection directory."""
        ...

    @property
    @abstractmethod
    def ntotal(self) -> int:
        """Number of vectors currently in the index."""
        ...