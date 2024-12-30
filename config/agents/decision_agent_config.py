"""Decision Agent configuration."""
from typing import Dict, Any
from pydantic import Field
from config.agents.agent_config_base import AgentConfigBase
from config.game_constants import ModelType
from langchain_core.language_models.chat_models import BaseChatModel

class DecisionAgentConfig(AgentConfigBase):
    """Configuration specific to DecisionAgent."""
    
    # Decision-making parameters
    model_name: str = Field(
        default=ModelType.DECISION,
        description="Model for decision making"
    )
    temperature: float = Field(
        default=0.0,  # More creative for decisions
        description="Temperature for decision making"
    )
    
    system_message: str = Field(
        default="""You are a decision-making agent for an interactive game book. Your role is to analyze user responses and game rules to make appropriate decisions that affect the game's progression.

You must return a JSON object with the following structure:
{
    "next_section": int,     # The section number to go to next (REQUIRED)
    "conditions": [],        # List of conditions to add/update
    "analysis": ""          # Brief analysis of the decision
}

Always ensure:
1. Your response is valid JSON
2. next_section is ALWAYS present and is a positive integer
3. If the user's choice directly leads to a section (type: "direct"), use that section number
4. If the choice depends on conditions or dice, evaluate them to determine next_section
5. conditions should only include new or updated conditions
6. analysis should be brief but explain why the decision was made""",
        description="System message for LLM"
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
