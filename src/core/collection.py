from typing import Any, cast
import numpy as np
import numpy.typing as npt

from src.storage.collection import CollectionStorage


class Collection:
    def __init__(self, storage: CollectionStorage) -> None:
        self._storage = storage
        
    def add_documents(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]]
    ) -> list[int]:
        """
        Add multiple documents to the collection with their vectors and metadata.

        Args:
            vectors: A list of vector representations for the documents.
            metadatas: A list of metadata dictionaries corresponding to each document.

        Returns:
            A list of IDs for the added documents.
        """
        if len(vectors) != len(metadatas):
            raise ValueError("number of vectors and metadatas must match")

        vector_array = cast(
            npt.NDArray[np.generic],
            np.asarray(vectors, dtype=self._storage.vectors.dtype),
        )
        if vector_array.ndim != 2:
            raise ValueError(f"vectors must be two-dimensional (got shape {vector_array.shape}, input={vectors})")
        if vector_array.shape[1] != self._storage.vectors.dim:
            raise ValueError(
                f"size mismatch: each vector in this collection must have dimension {self._storage.vectors.dim}"
            )

        return self._storage.add(vectors=vector_array, metadatas=metadatas)