from pydantic import BaseModel
from typing import Any


class Collection(BaseModel):
    name: str
    dim: int
    
class ListCollectionsResponse(BaseModel):
    collections: list[Collection]
    total: int
    
class CreateCollectionRequest(BaseModel):
    name: str
    dim: int
    
class AddDocumentRequest(BaseModel):
    vector: list[float]
    metadata: dict[str, Any]

class AddDocumentResponse(BaseModel):
    id: int