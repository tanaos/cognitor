from dataclasses import dataclass
from typing import Any


@dataclass
class Document:
    id: str
    vector: list[float]
    text: str
    metadata: dict[str, Any]
    
@dataclass 
class CollectionInfo:
    name: str
    dim: int
    doc_count: int