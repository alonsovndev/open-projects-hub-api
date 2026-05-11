"""Dashboard DTOs for stats."""
from typing import List, Optional

from pydantic import BaseModel, Field


class ProjectSummary(BaseModel):
    """DTO for recent project summary."""
    
    id: str
    name: str
    status: str
    created_at: str = Field(alias="createdAt")
    
    model_config = {"populate_by_name": True}


class StorySummary(BaseModel):
    """DTO for recent story summary."""
    
    id: str
    title: str
    status: str
    priority: str
    created_at: str = Field(alias="createdAt")
    
    model_config = {"populate_by_name": True}


class DashboardStatsResponse(BaseModel):
    """DTO for dashboard statistics response."""
    
    total_projects: int = Field(alias="totalProjects")
    active_projects: int = Field(alias="activeProjects")
    total_stories: int = Field(alias="totalStories")
    assigned_stories: int = Field(alias="assignedStories")
    completed_stories: int = Field(alias="completedStories")
    recent_projects: List[ProjectSummary] = Field(default_factory=list, alias="recentProjects")
    recent_stories: List[StorySummary] = Field(default_factory=list, alias="recentStories")
    
    model_config = {"populate_by_name": True}