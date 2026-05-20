from typing import Any, cast
import numpy as np
import numpy.typing as npt

from src.storage.collection import CollectionStorage


class Collection:
    """
    Manages operations on documents belonging to a specific collection.
    """
    
    def __init__(self, storage: CollectionStorage) -> None:
        self._storage = storage
        
    def add_documents(
        self, vectors: list[list[float]], metadatas: list[dict[str, Any]]
    ) -> list[str]:
        """
        Add multiple documents to the collection with their vectors and metadata.

        Args:
            vectors: A list of vector representations for the documents.
            metadatas: A list of metadata dictionaries corresponding to each document.

        Returns:
            A list of UUID strings for the added documents.
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

    def get_document(self, doc_id: str) -> tuple[list[float], dict[str, Any]]:
        """
        Retrieve a single document's vector and metadata by UUID.

        Args:
            doc_id: The UUID of the document.

        Returns:
            A tuple of (vector, metadata).
        """
        metadata = self._storage.get_metadata([doc_id])[0]
        if metadata is None:
            raise KeyError(f"Document with id {doc_id} does not exist")
        vector = self._storage.get_vectors([doc_id])[0].tolist()
        return vector, metadata

    def list_documents(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[tuple[str, list[float], dict[str, Any]]]:
        """
        List non-deleted documents in insertion order using offset/limit pagination.

        Args:
            offset: Number of non-deleted documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            A list of tuples in the form (id, vector, metadata).
        """
        if offset < 0:
            raise ValueError("offset must be greater than or equal to 0")
        if limit <= 0:
            raise ValueError("limit must be greater than 0")

        live_docs = self._storage.metadata.list_live(offset, limit)
        if not live_docs:
            return []

        self._storage.vectors.open("r")
        if self._storage.vectors.vectors is None:
            return []

        return [
            (doc_id, self._storage.vectors.vectors[vector_pos].tolist(), metadata)
            for doc_id, vector_pos, metadata in live_docs
        ]

    def delete_document(self, doc_id: str) -> None:
        """
        Delete a document by UUID. This will only remove the document's metadata record,
        effectively marking the document as deleted. The vector data will remain in storage
        but will be inaccessible through the API. Vectors can be physically removed later during
        a compact and rebuild process.

        Args:
            doc_id: The UUID of the document.
        """
        deleted = self._storage.delete_document(doc_id)
        if not deleted:
            raise KeyError(f"Document with id {doc_id} does not exist")

    def update_document(self, doc_id: str, metadata: dict[str, Any]) -> None:
        """
        Replace the metadata of an existing document.

        Args:
            doc_id: The UUID of the document.
            metadata: New metadata dictionary to store.

        Raises:
            KeyError: If the document does not exist or has been deleted.
        """
        if self._storage.get_metadata([doc_id])[0] is None:
            raise KeyError(f"Document with id {doc_id} does not exist")
        self._storage.metadata.update_metadata(doc_id, metadata)