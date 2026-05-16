import os
from sqlalchemy import Integer, Text, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column

from src.config.defaults import SQLLITE_DB_PATH


Base = declarative_base()


def _database_url() -> str:
    return os.getenv("DB_ENDPOINT", f"sqlite:///{SQLLITE_DB_PATH}")


db_engine: Engine = create_engine(_database_url(), future=True)


def init_db() -> None:
    Base.metadata.create_all(db_engine)


class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, nullable=False)