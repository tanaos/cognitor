from dataclasses import dataclass, field

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
    vector: Vector | None = field(default=None)

@dataclass 
class CollectionInfo:
    name: str
    dim: int
    doc_count: int