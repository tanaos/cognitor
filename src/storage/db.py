from sqlalchemy import  Integer, Text
from sqlalchemy.orm import Mapped, declarative_base, mapped_column


Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    metadata: Mapped[str] = mapped_column(Text, nullable=False)