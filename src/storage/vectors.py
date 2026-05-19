import numpy as np
from pathlib import Path
from typing import Literal

import numpy.typing as npt

MemMapMode = Literal["r", "r+", "w+", "c", "readonly", "readwrite", "write", "copyonwrite"]


class VectorStore:
    """
    Manages storage and retrieval of vectors using memory-mapped files.
    """
    
    # TODO: vector index should NOT be its position in the file, because compaction rewrites 
    # the file and reassigns IDs.
    
    def __init__(self, path: str, dim: int, dtype: npt.DTypeLike = np.float16):
        self.path = path
        self.dim = dim
        self.dtype: npt.DTypeLike = dtype
        self.file = Path(path) / "vectors.f16"

        self.vectors = None
        self.size = 0

    def load_size(self) -> int:
        """
        Load the current size of the vector store.
        
        Returns:
            int: Number of vectors currently stored.
        """
        if not self.file.exists():
            return 0

        itemsize = np.dtype(self.dtype).itemsize
        row_size = itemsize * self.dim
        byte_size = self.file.stat().st_size

        if row_size == 0 or byte_size % row_size != 0:
            raise ValueError("Vector file size is not aligned with vector dimensionality and dtype")

        return byte_size // row_size

    def _resize(self, new_size: int) -> None:
        """
        Resize the vector store to a new size.
        
        Args:
            new_size: The new size of the vector store.
        """
        if new_size < 0:
            raise ValueError("new_size must be non-negative")

        self.file.parent.mkdir(parents=True, exist_ok=True)

        itemsize = np.dtype(self.dtype).itemsize
        new_byte_size = new_size * self.dim * itemsize

        with self.file.open("a+b") as f:
            f.truncate(new_byte_size)

        self.size = new_size

        if new_size == 0:
            self.vectors = None
            return

        self.vectors = np.memmap(
            self.file,
            dtype=self.dtype,
            mode="r+",
            shape=(new_size, self.dim),
        )
        
    def open(self, mode: MemMapMode = "r+") -> None:
        """
        Open the vector store with the specified mode.
        
        Args:
            mode: Memory-mapped file mode.
        """
        self.size = self.load_size()

        if self.size == 0:
            self.vectors = None
            return

        self.vectors = np.memmap(
            self.file,
            dtype=self.dtype,
            mode=mode,
            shape=(self.size, self.dim)
        )

    def append(self, batch_vectors: np.ndarray):
        """
        Append a batch of vectors to the vector store.
        
        Args:
            batch_vectors: A 2D numpy array of shape (n, dim) containing the vectors to append.
        """
        if batch_vectors.ndim != 2 or batch_vectors.shape[1] != self.dim:
            raise ValueError(f"batch_vectors must have shape (n, {self.dim})")
        batch_size = len(batch_vectors)
        start = self.size

        self._resize(start + batch_size)

        assert self.vectors is not None
        self.vectors[start:start + batch_size] = batch_vectors
        self.vectors.flush()

    def truncate(self, size: int) -> None:
        """
        Shrink the vector store to ``size`` vectors, discarding any vectors
        beyond that index. Used by WAL recovery to roll back partial writes.

        Args:
            size: New number of vectors to retain (must be <= current size).
        """
        if size < 0:
            raise ValueError("size must be non-negative")
        if size > self.size:
            raise ValueError("truncate cannot grow the vector store")
        self._resize(size)

    def replace_all(self, vectors: np.ndarray) -> None:
        """
        Atomically replace the entire vector file with a new array.

        Writes to a sibling temp file first, then renames it over the current
        file so the operation is crash-safe at the filesystem level. The
        in-memory mmap is refreshed after the rename.

        Args:
            vectors: Array of shape (n, dim) to write.
        """
        if vectors.ndim != 2 or vectors.shape[1] != self.dim:
            raise ValueError(f"vectors must have shape (n, {self.dim})")

        new_count = len(vectors)
        tmp = self.file.with_suffix(".tmp")
        self.file.parent.mkdir(parents=True, exist_ok=True)

        if new_count > 0:
            arr = np.memmap(tmp, dtype=self.dtype, mode="w+", shape=(new_count, self.dim))
            arr[:] = vectors.astype(self.dtype)
            arr.flush()
            del arr
        else:
            tmp.write_bytes(b"")

        # Release current mmap before renaming over the file.
        if self.vectors is not None:
            del self.vectors
            self.vectors = None

        tmp.replace(self.file)
        self.size = new_count

        if new_count > 0:
            self.vectors = np.memmap(
                self.file, dtype=self.dtype, mode="r+", shape=(new_count, self.dim)
            )