import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional

from .db import Base, Document


class MetadataStore:
    """
    Manages storage and retrieval of document metadata using SQLite.
    """

    def __init__(self, path: str):
        db_path = Path(path) / "metadata.sqlite"
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
            # Check if document exists
            doc = session.query(Document).filter(Document.id == id).first()
            if doc:
                doc.metadata = json.dumps(metadata)
            else:
                doc = Document(id=id, metadata=json.dumps(metadata))
                session.add(doc)
            session.commit()
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
            return json.loads(doc.metadata) if doc else None
        finally:
            session.close()