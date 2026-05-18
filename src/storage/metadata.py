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
            # Check if document exists
            doc = session.query(Document).filter(Document.id == id).first()
            if doc:
                doc.metadata_json = json.dumps(metadata)
            else:
                doc = Document(id=id, metadata_json=json.dumps(metadata))
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
            return json.loads(doc.metadata_json) if doc else None
        finally:
            session.close()