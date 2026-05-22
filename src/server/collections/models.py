from pydantic import BaseModel, Field

from src.core.types import Vector, Metadata, DocumentId


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
    vectors: list[Vector]
    texts: list[str]
    metadatas: list[Metadata]

class UpdateDocumentRequest(BaseModel):
    metadata: Metadata

class AddDocumentResponse(BaseModel):
    ids: list[DocumentId]

class DocumentResponse(BaseModel):
    id: DocumentId
    vector: Vector
    metadata: Metadata
    text: str

class ListDocumentsResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int
    offset: int
    limit: int

class SearchRequest(BaseModel):
    query_vector: Vector
    top_k: int = Field(default=10, ge=1)
    filters: Metadata | None = None
    include_vectors: bool = False

class SearchResultResponse(BaseModel):
    id: DocumentId
    score: float
    text: str
    metadata: Metadata
    vector: Vector | None = None

class SearchResponse(BaseModel):
    results: list[SearchResultResponse]
    total: int