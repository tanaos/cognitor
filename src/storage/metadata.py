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

    def insert(self, id: int, metadata: dict[str, str]) -> None:
        """
        Insert or update a document's metadata.
        
        Args:
            id: Document ID
            metadata: Metadata dictionary
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(Document.id == id).first()
            if doc:
                doc.metadata_json = json.dumps(metadata)
            else:
                doc = Document(id=id, metadata_json=json.dumps(metadata))
                session.add(doc)
            session.commit()
        finally:
            session.close()

    def insert_batch(self, ids: list[int], metadatas: list[dict[str, str]]) -> None:
        """
        Insert a batch of documents in a single atomic transaction.

        If the write fails partway through, the entire batch is rolled back,
        preventing partial metadata from being committed without corresponding
        vectors.

        Args:
            ids: Document IDs.
            metadatas: Metadata dictionaries, one per ID.
        """
        session = self.SessionLocal()
        try:
            for id, metadata in zip(ids, metadatas):
                session.add(Document(id=id, metadata_json=json.dumps(metadata)))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_ids(self, ids: list[int]) -> None:
        """
        Delete all metadata rows for the given IDs in a single transaction.

        Used by WAL recovery to remove metadata that was committed but whose
        corresponding vectors were rolled back.

        Args:
            ids: Document IDs to delete.
        """
        session = self.SessionLocal()
        try:
            session.query(Document).filter(Document.id.in_(ids)).delete(
                synchronize_session=False
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get(self, id: int) -> Optional[dict[str, str]]:
        """
        Retrieve a document's metadata.
        
        Args:
            id: Document ID
            
        Returns:
            Metadata dictionary or None if not found
        """
        session = self.SessionLocal()
        try:
            doc = session.query(Document).filter(Document.id == id).first()
            return json.loads(doc.metadata_json) if doc else None
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

    def rewrite(self, ids: list[int], metadatas: list[dict[str, str]]) -> None:
        """
        Atomically replace all stored metadata with a new id/metadata mapping.

        Deletes every existing row and inserts the new rows in a single
        transaction. Used during compaction to reassign document IDs after
        soft-deleted vectors have been physically removed.

        Args:
            ids: New sequential document IDs.
            metadatas: Metadata dictionaries, one per ID.
        """
        session = self.SessionLocal()
        try:
            session.query(Document).delete()
            for id, metadata in zip(ids, metadatas):
                session.add(Document(id=id, metadata_json=json.dumps(metadata)))
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete(self, id: int) -> bool:
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