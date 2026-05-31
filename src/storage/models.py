from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .orm import Base



class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[str] = mapped_column(Text, primary_key=True)
    vector_pos: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    api_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False)