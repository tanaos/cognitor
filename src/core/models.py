from dataclasses import dataclass, field
from typing import Optional

from .types import Vector, Metadata, DocumentId


@dataclass
class Document:
    id: DocumentId
    vector: Vector
    text: str
    metadata: Metadata

@dataclass
class SearchResult:
    id: DocumentId
    score: float
    text: str
    metadata: Metadata
    vector: Optional[Vector] = field(default=None)

@dataclass 
class CollectionInfo:
    name: str
    dim: int
    doc_count: int
    emb_model: Optional[str] = field(default=None)