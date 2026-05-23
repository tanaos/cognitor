from typing import Optional

from pydantic import BaseModel, Field, model_validator

from src.core.types import Vector, Metadata, DocumentId


class Collection(BaseModel):
    name: str
    dim: int
    doc_count: int
    emb_model: Optional[str] = None

class ListCollectionsResponse(BaseModel):
    collections: list[Collection]
    total: int

class CreateCollectionRequest(BaseModel):
    name: str
    dim: int
    emb_model: Optional[str] = None

class AddDocumentRequest(BaseModel):
    vectors: Optional[list[Vector]] = None
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
    query_vector: Optional[Vector] = None
    query_text: Optional[str] = None
    top_k: int = Field(default=10, ge=1)
    filters: Optional[Metadata] = None
    include_vectors: bool = False

    @model_validator(mode="after")
    def _require_query(self) -> "SearchRequest":
        if self.query_vector is None and self.query_text is None:
            raise ValueError("either query_vector or query_text must be provided")
        return self

class SearchResultResponse(BaseModel):
    id: DocumentId
    score: float
    text: str
    metadata: Metadata
    vector: Optional[Vector] = None

class SearchResponse(BaseModel):
    results: list[SearchResultResponse]
    total: int