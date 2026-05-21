"""Suggestion type value object."""
from enum import Enum


class SuggestionType(str, Enum):
    """Type of AI suggestion."""
    
    TITLE = "title"
    DESCRIPTION = "description"
    CRITERIA = "criteria"
