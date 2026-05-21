from typing import List, Dict, Any
import uuid
import numpy as np
from .vectors import VectorStore
from .metadata import MetadataStore
from .wal import WriteAheadLog

from src.core.types import VectorArray


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
        self.wal: WriteAheadLog = WriteAheadLog(path)
        # Recover before opening: rolls back any uncommitted vectors and removes
        # orphaned metadata rows so both stores are consistent.
        self.wal.recover(self.vectors, self.metadata)

    def _generate_ids(self, n: int) -> List[str]:
        """
        Generate a list of unique UUID document IDs.
        
        Args:
            n: Number of IDs to generate.
            
        Returns:
            List of unique UUID strings.
        """
        return [str(uuid.uuid4()) for _ in range(n)]

    def add(
        self, vectors: np.ndarray, texts: list[str], metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Add a batch of vectors and their metadata to storage.
        
        Args:
            vectors: np.ndarray of shape (n, dim)
            texts: List of text contents, length n
            metadatas: List of metadata dicts, length n
            
        Returns:
            List of assigned UUID strings for the added vectors.
        """
        n = len(metadatas)
        ids = self._generate_ids(n)
        vector_start = self.vectors.size
        vector_positions = list(range(vector_start, vector_start + n))
        seq = self.wal.log_add_pending(vector_offset=vector_start, count=n)
        self.vectors.append(vectors)
        # Single transaction: either all metadata rows are committed or none are,
        # so a crash here cannot leave partial metadata without corresponding vectors.
        self.metadata.insert_batch(ids, vector_positions, texts, metadatas)
        self.wal.log_add_committed(seq, vector_offset=vector_start, count=n)
        return ids

    def get_vectors(self, ids: List[str]) -> VectorArray:
        """
        Retrieve vectors by their UUIDs.
        
        Args:
            ids: List of document UUIDs.
            
        Returns:
            VectorArray of shape (len(ids), dim) containing the requested vectors.
        """
        raw = self.metadata.get_vector_positions(ids)
        if any(p is None for p in raw):
            raise KeyError("One or more document IDs not found")
        positions: list[int] = [p for p in raw if p is not None]
        self.vectors.open("r")
        if self.vectors.vectors is None:
            raise ValueError("No vectors stored.")
        return self.vectors.vectors[positions]

    def get_metadata_and_text(
        self, ids: List[str]
    ) -> List[tuple[Dict[str, Any], str] | None]:
        """
        Retrieve metadata and text for a list of UUIDs.
        
        Args:
            ids: List of document UUIDs.
            
        Returns:
            List of tuples containing metadata dicts and text (or None if not found for an ID).
        """
        return [self.metadata.get(i) for i in ids]

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document's metadata record by UUID. This does not remove the vector from storage, 
        but marks the document as deleted by removing its metadata. Vectors can be physically
        removed during future compaction processes.
        
        Args:
            doc_id: Document UUID.
            
        Returns:
            True if deleted, False if not found.
        """
        return self.metadata.delete(doc_id)