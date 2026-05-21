"""
Shared pagination models for API responses.

Provides standard pagination envelope structure for list endpoints.
"""
from typing import TypeVar, Generic, List
from pydantic import BaseModel, Field, ConfigDict


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard pagination envelope for list endpoints.
    
    Contains pagination metadata and the list of items.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 42,
                "page": 1,
                "per_page": 20,
                "items": []
            }
        }
    )
    
    total: int = Field(..., description="Total number of items available", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    per_page: int = Field(..., description="Number of items per page", ge=1, le=100)
    items: List[T] = Field(..., description="List of items for current page")
