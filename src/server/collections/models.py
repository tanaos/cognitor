from pydantic import BaseModel
from typing import Any


class Collection(BaseModel):
    name: str
    dim: int
    doc_count: int
    
class ListCollectionsResponse(BaseModel):
    collections: list[Collection]
    total: int
    
class CreateCollectionRequest(BaseModel):
    name: str
    dim: int
    
class AddDocumentRequest(BaseModel):
    vectors: list[list[float]]
    metadata: list[dict[str, Any]]

class UpdateDocumentRequest(BaseModel):
    metadata: dict[str, Any]

class AddDocumentResponse(BaseModel):
    ids: list[int]

class DocumentResponse(BaseModel):
    id: int
    vector: list[float]
    metadata: dict[str, Any] | None

class ListDocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    offset: int
    limit: int