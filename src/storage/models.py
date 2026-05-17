from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from .orm import Base



class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metadata_json: Mapped[str] = mapped_column("metadata", Text, nullable=False)