from typing import cast, Optional
import numpy as np

from src.storage.collection import CollectionStorage
from src.core.models import Document, SearchResult
from src.core.types import Vector, Metadata, DocumentId, VectorArray
from src.core.exceptions import (
    DimensionMismatchError,
    DocumentNotFoundError,
    InvalidDocumentInputError,
)
from src.search.filters import FilterSpec


class Collection:
    """
    Manages operations on documents belonging to a specific collection.
    """

    def __init__(self, storage: CollectionStorage) -> None:
        self._storage = storage
        
    def add_documents(
        self, vectors: list[Vector], texts: list[str], metadatas: list[Metadata]
    ) -> list[DocumentId]:
        """
        Add multiple documents to the collection with their vectors, text and metadata.

        Args:
            vectors: A list of vector representations for the documents.
            texts: A list of text contents for the documents.
            metadatas: A list of metadata dictionaries corresponding to each document.

        Returns:
            A list of UUID strings for the added documents.
        """
        if len(vectors) != len(texts) or len(vectors) != len(metadatas):
            raise InvalidDocumentInputError("number of vectors, texts, and metadatas must match")

        vector_array = cast(
            VectorArray,
            np.asarray(vectors, dtype=self._storage.vectors.dtype),
        )
        if vector_array.ndim != 2:
            raise InvalidDocumentInputError(f"vectors must be two-dimensional (got shape {vector_array.shape}, input={vectors})")
        if vector_array.shape[1] != self._storage.vectors.dim:
            raise DimensionMismatchError(
                f"size mismatch: each vector in this collection must have dimension {self._storage.vectors.dim}"
            )

        return self._storage.add(vectors=vector_array, texts=texts, metadatas=metadatas)

    def get_document(self, doc_id: DocumentId) -> Document:
        """
        Retrieve a single document's vector, text and metadata by UUID.

        Args:
            doc_id: The UUID of the document.

        Returns:
            A Document object.
        """
        out = self._storage.get_metadata_and_text([doc_id])[0]
        if out is None:
            raise DocumentNotFoundError(doc_id)
        metadata, text = out
        vector = self._storage.get_vectors([doc_id])[0].tolist()
        return Document(id=doc_id, vector=vector, text=text, metadata=metadata)

    def list_documents(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> list[Document]:
        """
        List non-deleted documents in insertion order using offset/limit pagination.

        Args:
            offset: Number of non-deleted documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            A list of Document objects.
        """
        if offset < 0:
            raise InvalidDocumentInputError("offset must be greater than or equal to 0")
        if limit <= 0:
            raise InvalidDocumentInputError("limit must be greater than 0")

        live_docs = self._storage.metadata.list_live(offset, limit)
        if not live_docs:
            return []

        self._storage.vectors.open("r")
        if self._storage.vectors.vectors is None:
            return []

        return [
            Document(
                id=doc.id, vector=self._storage.vectors.vectors[doc.vector_pos].tolist(), 
                text=doc.text, metadata=doc.metadata
            ) for doc in live_docs
        ]

    def delete_document(self, doc_id: DocumentId) -> None:
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
            raise DocumentNotFoundError(doc_id)

    def update_document(self, doc_id: DocumentId, metadata: Metadata) -> None:
        """
        Replace the metadata of an existing document.

        Args:
            doc_id: The UUID of the document.
            metadata: New metadata dictionary to store.

        Raises:
            KeyError: If the document does not exist or has been deleted.
        """
        if self._storage.get_metadata_and_text([doc_id])[0] is None:
            raise DocumentNotFoundError(doc_id)
        self._storage.metadata.update_metadata(doc_id, metadata)

    def search(
        self,
        query_vector: Vector,
        top_k: int = 10,
        filters: Optional[FilterSpec] = None,
        include_vectors: bool = False,
    ) -> list[SearchResult]:
        """
        Search for the most similar documents to a query vector.

        Args:
            query_vector: Query vector with the same dimensionality as the collection.
            top_k: Maximum number of results to return.
            filters: Optional metadata equality filters, e.g. {"genre": "sci-fi"}.
            include_vectors: Whether to include raw vectors in the results.

        Returns:
            List of SearchResult objects ordered by descending similarity score.
        """
        from src.search.engine import SearchEngine

        if len(query_vector) != self._storage.vectors.dim:
            raise DimensionMismatchError(
                f"query vector must have dimension {self._storage.vectors.dim}"
            )

        engine = SearchEngine(
            index=self._storage.index,
            metadata_store=self._storage.metadata,
            vector_store=self._storage.vectors,
        )
        return engine.search(query_vector, top_k, filters, include_vectors)