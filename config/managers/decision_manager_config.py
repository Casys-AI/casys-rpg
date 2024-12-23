"""Decision Manager configuration."""
from pydantic import Field
from config.storage_config import StorageConfig

class DecisionManagerConfig(StorageConfig):
    """Configuration for the Decision Manager."""
    
    validate_responses: bool = Field(
        default=True,
        description="Validate responses against rules"
    )
