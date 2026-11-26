from pydantic import BaseModel
from typing import TypeVar, Generic, Optional, List, Any
from datetime import datetime

T = TypeVar("T")

class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T
    message: Optional[str] = None

class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail

class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    data: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
