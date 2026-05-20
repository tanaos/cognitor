import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from src.storage.vectors import VectorStore
    from src.storage.metadata import MetadataStore


@dataclass
class WALEntry:
    seq: int
    op: Literal["ADD", "DELETE"]
    status: Literal["PENDING", "COMMITTED"]
    vector_offset: int = 0   # For ADD: index of first new vector in the file
    count: int = 0           # For ADD: number of vectors in this batch
    doc_id: str = ""         # For DELETE: document UUID


class WriteAheadLog:
    """
    Append-only Write-Ahead Log for crash-safe storage operations.

    Each mutating operation is bracketed by a PENDING entry written before the
    operation and a COMMITTED entry written after. On startup ``recover()``
    detects PENDING entries that were never committed and rolls back the vector
    file to the last safe offset.

    DELETE operations are backed by SQLite which is ACID on its own, so the WAL
    entry is purely informational, as no vector-level rollback is required for
    deletes.

    File format: one JSON object per line (JSONL) at ``{path}/wal.jsonl``.
    """

    WAL_FILENAME = "wal.jsonl"

    def __init__(self, path: str) -> None:
        self._path = Path(path) / self.WAL_FILENAME
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._seq = self._load_max_seq()

    def _iter_entries(self):
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield WALEntry(**json.loads(line))
                except (json.JSONDecodeError, TypeError):
                    continue

    def _append(self, entry: WALEntry) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry)) + "\n")
            f.flush()

    def _load_max_seq(self) -> int:
        return max((e.seq for e in self._iter_entries()), default=0)

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def log_add_pending(self, vector_offset: int, count: int) -> int:
        """
        Record a pending ADD operation before writing to storage.

        Args:
            vector_offset: Current size of the vector file (index of the first
                new vector that is about to be appended).
            count: Number of vectors being added.

        Returns:
            Sequence number to pass to ``log_add_committed``.
        """
        with self._lock:
            seq = self._next_seq()
            self._append(
                WALEntry(
                    seq=seq, op="ADD", status="PENDING",
                    vector_offset=vector_offset, count=count
                )
            )
            return seq

    def log_add_committed(self, seq: int, vector_offset: int, count: int) -> None:
        """
        Record that a previously pending ADD has been fully committed.
        
        Args:
            seq: Sequence number returned by the corresponding ``log_add_pending``.
            vector_offset: Index of the first new vector that was appended.
            count: Number of vectors that were added.
        """
        with self._lock:
            self._append(
                WALEntry(
                    seq=seq, op="ADD", status="COMMITTED",
                    vector_offset=vector_offset, count=count
                )
            )

    def log_delete_pending(self, doc_id: str) -> int:
        """
        Record a pending DELETE operation before writing to storage.
        
        Args:
            doc_id: UUID of the document being deleted.

        Returns:
            Sequence number to pass to ``log_delete_committed``.
        """
        with self._lock:
            seq = self._next_seq()
            self._append(
                WALEntry(
                    seq=seq, op="DELETE", status="PENDING", doc_id=doc_id
                )
            )
            return seq

    def log_delete_committed(self, seq: int, doc_id: str) -> None:
        """
        Record that a previously pending DELETE has been fully committed.
        
        Args:
            seq: Sequence number returned by the corresponding ``log_delete_pending``.
            doc_id: UUID of the document that was deleted.
        """
        with self._lock:
            self._append(
                WALEntry(
                    seq=seq, op="DELETE", status="COMMITTED", doc_id=doc_id
                )
            )

    def recover(self, vector_store: "VectorStore", metadata_store: "MetadataStore") -> None:
        """
        Roll back any uncommitted ADD operations after a crash.

        Scans the WAL for PENDING ADD entries that have no matching COMMITTED
        entry and performs a two-phase rollback:

        1. Deletes any metadata rows whose ``vector_pos`` falls within the range
           of an uncommitted batch. This handles the case where metadata was
           committed to SQLite but the process crashed before ``WAL COMMITTED``
           was written.

        2. Truncates the vector file back to the smallest unconfirmed write
           offset, discarding any partially-written vectors.

        DELETE operations do not need vector-level recovery because the metadata
        is managed by SQLite (which has its own crash recovery).

        Args:
            vector_store: The ``VectorStore`` instance whose file may need truncating.
            metadata_store: The ``MetadataStore`` used to remove orphaned metadata rows.
        """
        if not self._path.exists():
            return

        all_entries = list(self._iter_entries())
        committed_seqs = {e.seq for e in all_entries if e.status == "COMMITTED"}
        pending_adds = [
            e for e in all_entries
            if e.op == "ADD" and e.status == "PENDING" and e.seq not in committed_seqs
        ]

        if not pending_adds:
            return

        # Delete any metadata rows whose vector_pos falls within an uncommitted batch.
        for e in pending_adds:
            metadata_store.delete_by_vector_pos_range(e.vector_offset, e.count)

        # Truncate to the earliest un-committed write offset.
        safe_size = min(e.vector_offset for e in pending_adds)
        if vector_store.load_size() > safe_size:
            vector_store.truncate(safe_size)

    def compact(self) -> None:
        """
        Rewrite the WAL keeping only entries that have not yet been committed. This prevents the
        WAL from growing indefinitely with obsolete entries after many operations and compactions.
        This operation is performed after a collection compaction.
        """
        with self._lock:
            all_entries = list(self._iter_entries())
            committed_seqs = {e.seq for e in all_entries if e.status == "COMMITTED"}
            surviving = [
                e for e in all_entries
                if not (e.seq in committed_seqs)
            ]
            tmp = self._path.with_suffix(".tmp")
            with tmp.open("w", encoding="utf-8") as f:
                for entry in surviving:
                    f.write(json.dumps(asdict(entry)) + "\n")
            tmp.replace(self._path)
