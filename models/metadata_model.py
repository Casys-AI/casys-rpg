"""Models for metadata."""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """Metadata for game content."""
    title: str = Field(description="Title of the content")
    description: str = Field(description="Description of the content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing content")
    author: str = Field(description="Author of the content")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation date")
    
