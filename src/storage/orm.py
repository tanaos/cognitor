import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base

from src.config.defaults import SQLLITE_DB_PATH


Base = declarative_base()


def _database_url() -> str:
    return os.getenv("DB_ENDPOINT", f"sqlite:///{SQLLITE_DB_PATH}")


db_engine: Engine = create_engine(_database_url(), future=True)


def init_db() -> None:
    Base.metadata.create_all(db_engine)