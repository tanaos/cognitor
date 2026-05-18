from typing import Any, cast
import numpy as np
import numpy.typing as npt

from src.storage.collection import CollectionStorage


class Collection:
    def __init__(self, storage: CollectionStorage) -> None:
        self._storage = storage

    def add_document(
        self, vector: list[float], metadata: dict[str, Any]
    ) -> int:
        """
        Add a single document to the collection with its vector and metadata.

        Args:
            vector: The vector representation of the document.
            metadata: Additional metadata associated with the document.

        Returns:
            The ID of the added document.
        """
        return self.add_documents(vectors=[vector], metadatas=[metadata])[0]
        
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
        vector_array = cast(
            npt.NDArray[np.generic],
            np.asarray(vectors, dtype=self._storage.vectors.dtype),
        )
        if vector_array.ndim != 2:
            raise ValueError("vectors must be two-dimensional")
        if vector_array.shape[1] != self._storage.vectors.dim:
            raise ValueError(
                f"each vector must have dimension {self._storage.vectors.dim}"
            )
        if vector_array.shape[0] != len(metadatas):
            raise ValueError("number of vectors and metadatas must match")

        return self._storage.add(vectors=vector_array, metadatas=metadatas)