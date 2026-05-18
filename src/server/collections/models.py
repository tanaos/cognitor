from pydantic import BaseModel


class Collection(BaseModel):
    name: str
    dim: int
    
class ListCollectionsResponse(BaseModel):
    collections: list[Collection]
    total: int
    
class CreateCollectionRequest(BaseModel):
    name: str
    dim: int