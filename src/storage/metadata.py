import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

from src.storage.models import Document
from src.storage.orm import Base
from src.config.defaults import SQLLITE_DB_PATH


class MetadataStore:
    """
    Manages storage and retrieval of document metadata using SQLite.
    """

    def __init__(self, path: str):
        db_path = Path(path) / SQLLITE_DB_PATH
        db_url = f"sqlite:///{db_path}"
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def update_metadata(self, id: str, metadata: dict[str, str]) -> None:
        """
        Update the metadata of an existing document. The vector_pos is preserved.

        Args:
            id: Document UUID
            metadata: New metadata dictionary

        Raises:
            KeyError: If no document with the given ID exists.
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(Document.id == id).first()
            if doc is None:
                raise KeyError(f"Document with id {id} does not exist")
            doc.metadata_json = json.dumps(metadata)
            session.commit()
        finally:
            session.close()

    def insert_batch(
        self, ids: list[str], vector_positions: list[int], texts: list[str], 
        metadatas: list[dict[str, str]]
    ) -> None:
        """
        Insert a batch of documents in a single atomic transaction.

        If the write fails partway through, the entire batch is rolled back,
        preventing partial metadata from being committed without corresponding
        vectors.

        Args:
            ids: Stable document UUIDs.
                vector_positions: Position of each document's vector in the vector file.
            texts: Text contents, one per ID.
            metadatas: Metadata dictionaries, one per ID.
        """
        session = self.SessionLocal()
        try:
            for i in range(len(ids)):
                session.add(
                    Document(
                        id=ids[i], vector_pos=vector_positions[i], text=texts[i],
                        metadata_json=json.dumps(metadatas[i])
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_by_vector_pos_range(self, offset: int, count: int) -> None:
        """
        Delete all metadata rows whose vector_pos falls in [offset, offset + count).

        Used by WAL recovery to remove metadata rows for vectors that were
        written to the file but whose ADD operation was never committed.

        Args:
            offset: First vector position to remove.
            count: Number of consecutive positions to remove.
        """
        session = self.SessionLocal()
        try:
            session.query(Document).filter(
                Document.vector_pos >= offset,
                Document.vector_pos < offset + count,
            ).delete(synchronize_session=False)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_vector_positions(self, ids: list[str]) -> list[Optional[int]]:
        """
        Return the vector file position for each document UUID.

        Args:
            ids: Document UUIDs to look up.

        Returns:
            List of vector positions, or None for any ID not found.
        """
        session = self.SessionLocal()
        try:
            rows = session.query(
                Document.id, Document.vector_pos
            ).filter(Document.id.in_(ids)).all()
            pos_map = {row.id: row.vector_pos for row in rows}
            return [pos_map.get(i) for i in ids]
        finally:
            session.close()

    def get(self, id: str) -> Optional[tuple[dict[str, str], str]]:
        """
        Retrieve a document's metadata and text.
        
        Args:
            id: Document UUID
            
        Returns:
            Metadata dictionary and text or None if not found
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(Document.id == id).first()
            return (json.loads(doc.metadata_json), doc.text) if doc else None
        finally:
            session.close()

    def count(self) -> int:
        """
        Return the number of live (non-deleted) documents.

        Returns:
            Row count of the documents table.
        """
        session = self.SessionLocal()
        try:
            return session.query(Document).count()
        finally:
            session.close()

    def list_live(self, offset: int, limit: int) -> list[Document]:
        """
        Return a page of live documents ordered by insertion (id).

        Args:
            offset: Number of documents to skip.
            limit: Maximum number of documents to return.

        Returns:
            List of Document objects.
        """
        session = self.SessionLocal()
        try:
            rows = (
                session.query(Document)
                .order_by(Document.id)
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [
                Document(
                    id=row.id, vector_pos=row.vector_pos, text=row.text, 
                    metadata=json.loads(row.metadata_json)
                ) for row in rows]
        finally:
            session.close()

    def list_all_live(self) -> list[Document]:
        """
        Return all live documents ordered by id.

        Used during compaction to enumerate every document that needs to be
        kept in the rewritten vector file.

        Returns:
            List of Document objects.
        """
        session = self.SessionLocal()
        try:
            rows = session.query(Document).order_by(Document.id).all()
            return [
                Document(
                    id=row.id, vector_pos=row.vector_pos, text=row.text, 
                    metadata=json.loads(row.metadata_json)
                ) for row in rows]
        finally:
            session.close()

    def get_by_vector_positions(self, positions: list[int]) -> list[Optional[Document]]:
        """
        Retrieve documents by their vector file positions.

        Args:
            positions: List of vector_pos values to look up.

        Returns:
            List of Document objects in the same order as positions, or None for
            any position that has no live (non-deleted) document.
        """
        session = self.SessionLocal()
        try:
            rows = session.query(Document).filter(
                Document.vector_pos.in_(positions)
            ).all()
            pos_map = {
                row.vector_pos: Document(
                    id=row.id, vector_pos=row.vector_pos, text=row.text,
                    metadata=json.loads(row.metadata_json),
                )
                for row in rows
            }
            return [pos_map.get(p) for p in positions]
        finally:
            session.close()

    def rewrite(self, live_docs: list[Document]) -> None:
        """
        Atomically replace all stored metadata with updated vector positions.

        Deletes every existing row and reinserts with the new ``vector_pos``
        values in a single transaction. Document UUIDs are preserved; only
        ``vector_pos`` changes to reflect the compacted file layout.

        Args:
            live_docs: List of Document objects.
        """
        session = self.SessionLocal()
        try:
            session.query(Document).delete()
            for doc in live_docs:
                session.add(
                    Document(
                        id=doc.id, vector_pos=doc.vector_pos, text=doc.text, 
                        metadata_json=json.dumps(doc.metadata)
                    )
                )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, id: str) -> bool:
        """
        Delete a document's metadata record.

        Args:
            id: Document ID

        Returns:
            True if the record was deleted, False if it did not exist.
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(Document.id == id).first()
            if doc is None:
                return False
            session.delete(doc)
            session.commit()
            return True
        finally:
            session.close()