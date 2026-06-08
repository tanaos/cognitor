from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path
import numpy as np

from .vectors import VectorStore
from .metadata import MetadataStore
from .wal import WriteAheadLog

from src.indexes.faiss_hnsw import FaissHNSWIndex
from src.core.types import VectorArray
from src.config.defaults import INDEX_FILE


class CollectionStorage:
    """
    Manages storage-level operations on vectors and their associated metadata.
    """

    def __init__(self, path: str, dim: int, load_index: bool = True) -> None:
        """
        Initialize the collection storage.
        
        Args:
            path: Directory path for storage files.
            dim: Dimensionality of the vectors.
        """
        self.path = path
        self.vectors: VectorStore = VectorStore(path, dim)
        self.metadata: MetadataStore = MetadataStore(path)
        self.wal: WriteAheadLog = WriteAheadLog(path)
        # Recover before opening: rolls back any uncommitted vectors and removes
        # orphaned metadata rows so both stores are consistent.
        self.wal.recover(self.vectors, self.metadata)
        # Sync size from disk so that add() computes the correct vector_start.
        # VectorStore.__init__ leaves size=0; WAL recovery only updates it when
        # it actually truncates (crash path). On a clean startup the field stays
        # 0, causing every add() to truncate the file back to position 0 and
        # overwrite all previously stored vectors.
        self.vectors.size = self.vectors.load_size()
        self.index: FaissHNSWIndex = FaissHNSWIndex(dim)
        self._index_loaded = False
        if load_index:
            self.ensure_index_loaded()

    def ensure_index_loaded(self) -> None:
        """
        Load the persisted index (or rebuild it) on first use.
        """
        if self._index_loaded:
            return

        index_file = Path(self.path) / INDEX_FILE
        if index_file.exists():
            self.index.load(self.path)
        else:
            self._rebuild_index()
        self._index_loaded = True

    def _rebuild_index(self) -> None:
        """
        Build the FAISS index from scratch using the current vector store and metadata.
        """
        docs = self.metadata.list_all_live()
        if not docs:
            return
        self.vectors.open("r")
        if self.vectors.vectors is None:
            return
        positions = np.array([doc.vector_pos for doc in docs], dtype=np.int64)
        vectors_f32 = self.vectors.vectors[positions].astype(np.float32)
        self.index.rebuild(positions, vectors_f32)
        self.index.save(self.path)

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

        self.ensure_index_loaded()
        positions_arr = np.array(vector_positions, dtype=np.int64)
        self.index.add(positions_arr, vectors.astype(np.float32))
        self.index.save(self.path)

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
    ) -> List[Optional[tuple[Dict[str, Any], str]]]:
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