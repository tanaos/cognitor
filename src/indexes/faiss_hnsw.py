from pathlib import Path
import faiss
import numpy as np

from .base import VectorIndex

from src.config.defaults import INDEX_FILE


class FaissHNSWIndex(VectorIndex):
    """
    A vector index implementation using FAISS's HNSW algorithm.
    """

    def __init__(
        self,
        dim: int,
        m: int = 32, # 16, 32, 64
        ef_construction: int = 200, # 100, 200, 400
        ef_search: int = 50, # 32, 50, 128
    ) -> None:
        self.dim = dim
        # Using IndexIDMap to associate FAISS's internal vector IDs with our vector_pos IDs.
        self._index: faiss.IndexIDMap = self._make_index(m, ef_construction, ef_search)

    def _make_index(self, m: int, ef_construction: int, ef_search: int) -> faiss.IndexIDMap:
        """
        Create a new FAISS HNSW index with the given parameters. The HNSW index is wrapped in an 
        IndexIDMap to manage our own vector_pos IDs.
        
        Args:
            m: The number of neighbors in the HNSW graph (higher values lead to better recall at 
                the cost of increased memory usage; typical values are 16, 32, 64).
            ef_construction: The size of the dynamic list for construction (higher values lead to 
                better recall at the cost of longer indexing time; typical values are 100, 200, 400).
            ef_search: The size of the dynamic list for searching (higher values lead to better 
                recall at the cost of longer search time; typical values are 32, 50, 128).
                
        Returns:
            A configured FAISS IndexIDMap wrapping an HNSW index.
        """
        
        hnsw = faiss.IndexHNSWFlat(self.dim, m) # Inner HNSW index with L2 distance 
        hnsw.hnsw.efConstruction = ef_construction
        hnsw.hnsw.efSearch = ef_search
        return faiss.IndexIDMap(hnsw) # Wrap in IndexIDMap to manage our own IDs

    @property
    def ntotal(self) -> int:
        """
        The number of vectors currently in the index.
        """
        
        return self._index.ntotal

    def add(self, positions: np.ndarray, vectors: np.ndarray) -> None:
        """
        Add vectors with their corresponding vector_pos IDs to the index.
        
        Args:
            positions: A 1D numpy array of vector_pos IDs corresponding to the vectors.
            vectors: A 2D numpy array of shape (n, dim) containing the vectors to be added.
        """
        
        self._index.add_with_ids(
            vectors.astype(np.float32), # FAISS requires float32 input
            positions.astype(np.int64), # FAISS requires int64 IDs
        )

    def search(self, query: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        """
        Search the index for the nearest neighbors of the query vector.
        
        Args:
            query: A 1D numpy array representing the query vector.
            top_k: The number of nearest neighbors to retrieve.
            
        Returns:
            A tuple containing two 1D numpy arrays:
            - scores: The similarity scores of the nearest neighbors.
            - ids: The vector_pos IDs of the nearest neighbors.
        """
        
        query_f32 = query.astype(np.float32).reshape(1, -1) # FAISS expects 2D input for search
        scores, ids = self._index.search(query_f32, top_k)
        return scores[0], ids[0]

    def rebuild(self, positions: np.ndarray, vectors: np.ndarray) -> None:
        """
        Discard the current index and rebuild it from scratch using the provided vectors and their 
        corresponding vector_pos IDs. This is useful for defragmenting the index after deletions.
        
        Args:
            positions: A 1D numpy array of vector_pos IDs corresponding to the vectors.
            vectors: A 2D numpy array of shape (n, dim) containing the vectors to be indexed.
        """
        
        # Downcast the index to access HNSW-specific parameters
        inner: faiss.IndexHNSWFlat = faiss.downcast_index(self._index.index)
        new_index = self._make_index(
            m=inner.hnsw.nb_neighbors(0),
            ef_construction=inner.hnsw.efConstruction,
            ef_search=inner.hnsw.efSearch,
        )
        self._index = new_index
        if len(positions) > 0:
            self.add(positions, vectors)

    def save(self, path: str) -> None:
        """
        Persist the index to the given collection directory.
        
        Args:
            path: The directory where the index should be saved.
        """
        
        faiss.write_index(self._index, str(Path(path) / INDEX_FILE))

    def load(self, path: str) -> None:
        """
        Load the index from the given collection directory.
        
        Args:
            path: The directory from which the index should be loaded.
        """
        self._index = faiss.read_index(str(Path(path) / INDEX_FILE))