from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

class ResponseBase(BaseModel):
    success: bool = True
    message: str = "OK"

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    per_page: int