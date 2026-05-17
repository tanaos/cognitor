from pydantic import BaseModel
from typing import Optional


class Collection(BaseModel):
    name: str
    description: Optional[str] = None
    
class ListCollectionsResponse(BaseModel):
    collections: list[Collection]
    total: int