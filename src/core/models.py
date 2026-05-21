from dataclasses import dataclass

from .types import Vector, Metadata, DocumentId


@dataclass
class Document:
    id: DocumentId
    vector: Vector
    text: str
    metadata: Metadata
    
@dataclass 
class CollectionInfo:
    name: str
    dim: int
    doc_count: int