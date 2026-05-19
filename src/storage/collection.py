
from typing import List, Dict, Any
import numpy as np
from .vectors import VectorStore
from .metadata import MetadataStore


class CollectionStorage:
    """
    Manages storage-level operations on vectors and their associated metadata.
    """

    def __init__(self, path: str, dim: int) -> None:
        """
        Initialize the collection storage.
        
        Args:
            path: Directory path for storage files.
            dim: Dimensionality of the vectors.
        """
        self.vectors: VectorStore = VectorStore(path, dim)
        self.metadata: MetadataStore = MetadataStore(path)
        self.id_counter: int = self.vectors.load_size()

    def _generate_ids(self, n: int) -> List[int]:
        """
        Generate a list of unique integer IDs.
        
        Args:
            n: Number of IDs to generate.
            
        Returns:
            List of unique integer IDs.
        """
        ids = list(range(self.id_counter, self.id_counter + n))
        self.id_counter += n
        return ids

    def add(self, vectors: np.ndarray, metadatas: List[Dict[str, Any]]) -> List[int]:
        """
        Add a batch of vectors and their metadata to storage.
        
        Args:
            vectors: np.ndarray of shape (n, dim)
            metadatas: List of metadata dicts, length n
            
        Returns:
            List of assigned integer IDs for the added vectors.
        """
        n = len(metadatas)
        ids = self._generate_ids(n)
        self.vectors.append(vectors)
        for i, meta in zip(ids, metadatas):
            self.metadata.insert(i, meta)
        return ids

    def get_vectors(self, ids: List[int]) -> np.ndarray:
        """
        Retrieve vectors by their IDs.
        
        Args:
            ids: List of integer IDs.
            
        Returns:
            np.ndarray of shape (len(ids), dim) containing the requested vectors.
        """
        self.vectors.open("r")
        if self.vectors.vectors is None:
            raise ValueError("No vectors stored.")
        return self.vectors.vectors[ids]

    def get_metadata(self, ids: List[int]) -> List[Dict[str, Any] | None]:
        """
        Retrieve metadata for a list of IDs.
        
        Args:
            ids: List of integer IDs.
            
        Returns:
            List of metadata dicts (or None if not found for an ID).
        """
        return [self.metadata.get(i) for i in ids]

    def delete_document(self, doc_id: int) -> bool:
        """
        Delete a document's metadata record by ID. This does not remove the vector from storage, 
        but marks the document as deleted by removing its metadata. Vectors can be physically
        removed during future compaction processes.
        
        Args:
            doc_id: Integer document ID.
            
        Returns:
            True if deleted, False if not found.
        """
        return self.metadata.delete(doc_id)