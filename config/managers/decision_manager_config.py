"""
Configuration for the Decision Manager
"""
from pydantic import BaseModel, Field

class DecisionManagerConfig(BaseModel):
    """Configuration for the Decision Manager."""
    
    # Cache settings
    cache_enabled: bool = Field(
        default=True,
        description="Enable caching of decisions"
    )
    
    # Debug settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    # Validation settings
    validate_responses: bool = Field(
        default=True,
        description="Validate responses against rules"
    )
