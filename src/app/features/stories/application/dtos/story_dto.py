"""Story DTOs for request and response."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateStoryRequest(BaseModel):
    """DTO for creating a story."""
    
    title: str = Field(..., min_length=1, max_length=255, description="Story title")
    description: Optional[str] = Field(None, description="Story description")
    project_id: str = Field(..., description="Parent project ID (UUID)")
    priority: Optional[str] = Field("medium", description="Priority: low, medium, high")
    points: Optional[int] = Field(None, ge=0, le=100, description="Story points (0-100)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Implement user login",
                    "description": "Add authentication flow with JWT tokens",
                    "project_id": "550e8400-e29b-41d4-a716-446655440001",
                    "priority": "high",
                    "points": 5,
                }
            ]
        }
    }


class UpdateStoryRequest(BaseModel):
    """DTO for updating a story."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Story title")
    description: Optional[str] = Field(None, description="Story description")
    status: Optional[str] = Field(None, description="Status: todo, in_progress, done")
    priority: Optional[str] = Field(None, description="Priority: low, medium, high")
    points: Optional[int] = Field(None, ge=0, le=100, description="Story points (0-100)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Updated title",
                    "status": "in_progress",
                    "points": 8,
                }
            ]
        }
    }


class AssignStoryRequest(BaseModel):
    """DTO for assigning a story to a user."""
    
    user_id: str = Field(..., description="User ID to assign story to (UUID)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440002",
                }
            ]
        }
    }


class StoryResponse(BaseModel):
    """DTO for story response."""
    
    id: str = Field(..., description="Story ID (UUID)")
    title: str = Field(..., description="Story title")
    description: Optional[str] = Field(None, description="Story description")
    project_id: str = Field(..., description="Parent project ID")
    created_by: str = Field(..., description="Creator user ID")
    assigned_to: Optional[str] = Field(None, description="Assigned user ID")
    status: str = Field(..., description="Status: todo, in_progress, done")
    priority: str = Field(..., description="Priority: low, medium, high")
    points: Optional[int] = Field(None, description="Story points")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440100",
                    "title": "Implement user login",
                    "description": "Add authentication flow",
                    "project_id": "550e8400-e29b-41d4-a716-446655440001",
                    "created_by": "550e8400-e29b-41d4-a716-446655440001",
                    "assigned_to": "550e8400-e29b-41d4-a716-446655440002",
                    "status": "todo",
                    "priority": "high",
                    "points": 5,
                    "created_at": "2026-05-09T12:00:00Z",
                    "updated_at": "2026-05-09T12:00:00Z",
                }
            ]
        }
    }