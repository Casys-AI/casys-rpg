"""Decision Agent configuration."""
from typing import Dict, Any
from pydantic import Field
from config.agents.agent_config_base import AgentConfigBase
from config.game_constants import ModelType

class DecisionAgentConfig(AgentConfigBase):
    """Configuration specific to DecisionAgent."""
    
    # Decision-making parameters
    model_name: str = Field(
        default=ModelType.DECISION,
        description="Model for decision making"
    )
    temperature: float = Field(
        default=0.7,  # More creative for decisions
        description="Temperature for decision making"
    )
    
    # Validation settings
    validate_choices: bool = Field(
        default=True,
        description="Validate user choices against rules"
    )
    strict_mode: bool = Field(
        default=False,
        description="Enforce strict rule validation"
    )
    
    # Response formatting
    format_responses: bool = Field(
        default=True,
        description="Format decision responses for display"
    )
