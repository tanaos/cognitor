from pydantic import BaseModel

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