from typing import Any, cast
import numpy as np
import numpy.typing as npt

from src.storage.collection import CollectionStorage


class Collection:
    """
    Manages collection-level operations on documents. Storage-level operations should be performed
    through the underlying CollectionStorage instance.
    """
    
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

    def get_document(self, doc_id: int) -> tuple[list[float], dict[str, Any] | None]:
        """
        Retrieve a single document's vector and metadata by ID. If the metadata is None, it means
        the document has been deleted and should not be accessible through the API.

        Args:
            doc_id: The integer ID of the document.

        Returns:
            A tuple of (vector, metadata).
        """
        if doc_id < 0 or doc_id >= self._storage.id_counter:
            raise KeyError(f"Document with id {doc_id} does not exist")
        metadata = self._storage.get_metadata([doc_id])[0]
        if metadata is None:
            raise KeyError(f"Document with id {doc_id} does not exist")
        vector = self._storage.get_vectors([doc_id])[0].tolist()
        return vector, metadata

    def delete_document(self, doc_id: int) -> None:
        """
        Delete a document by ID. This will only remove the document's metadata record,
        effectively marking the document as deleted. The vector data will remain in storage
        but will be inaccessible through the API. Vectors can be physically removed later during
        a compact and rebuild process.

        Args:
            doc_id: The integer ID of the document.
        """
        if doc_id < 0 or doc_id >= self._storage.id_counter:
            raise KeyError(f"Document with id {doc_id} does not exist")
        deleted = self._storage.delete_document(doc_id)
        if not deleted:
            raise KeyError(f"Document with id {doc_id} does not exist")

    def update_document(self, doc_id: int, metadata: dict[str, Any]) -> None:
        """
        Replace the metadata of an existing document.

        Args:
            doc_id: The integer ID of the document.
            metadata: New metadata dictionary to store.

        Raises:
            KeyError: If the document does not exist or has been deleted.
        """
        if doc_id < 0 or doc_id >= self._storage.id_counter:
            raise KeyError(f"Document with id {doc_id} does not exist")
        if self._storage.get_metadata([doc_id])[0] is None:
            raise KeyError(f"Document with id {doc_id} does not exist")
        self._storage.metadata.insert(doc_id, metadata)