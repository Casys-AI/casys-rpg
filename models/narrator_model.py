"""
Narrator Model Module
Defines the model for narrative content.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class SourceType(str, Enum):
    """Type of content source."""
    RAW = "raw"        # Content loaded from source file
    PROCESSED = "processed"  # Content processed by agent
    ERROR = "error"    # Error state

class NarratorModel(BaseModel):
    """Model for a narrative section."""
    
    section_number: int = Field(..., gt=0, description="Section number")
    content: str = Field(default="", description="Section content")
    source_type: SourceType = Field(default=SourceType.RAW, description="Source type")
    error: Optional[str] = Field(default=None, description="Error message if present")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp")

    class Config:
        """Model configuration."""
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
