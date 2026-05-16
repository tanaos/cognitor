from pydantic import BaseModel
from typing import Optional, Union, Any


class ErrorResponse(BaseModel):
    message: Optional[str]
    details: Optional[Union[dict[Any, Any], str]] = None