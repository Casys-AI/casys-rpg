"""Rules Agent configuration."""
from pydantic import Field
from config.agents.agent_config_base import AgentConfigBase
from config.game_constants import ModelType

class RulesAgentConfig(AgentConfigBase):
    """Configuration specific to RulesAgent."""
    model_name: str = Field(
        default=ModelType.RULES,
        description="Model for rules interpretation"
    )
    temperature: float = Field(
        default=0.0,  # Deterministic for rules
        description="Temperature for rules interpretation"
    )
    system_message: str = Field(
        default="""You are a rules analyst for an interactive game book.

Your task is to analyze game sections and extract rules in a structured JSON format.
You must return a JSON object with the following structure:
{
    "needs_dice": true|false,        # Whether a dice roll is needed
    "dice_type": "combat"|"chance"|"none",  # Type of dice roll required
    "conditions": ["condition1", "condition2", ...],  # List of conditions that apply
    "next_sections": [1, 2, ...],    # List of possible next section numbers
    "choices": ["choice1", "choice2", ...],  # List of available choices
    "rules_summary": "Summary of the rules"  # Brief summary of the section's rules
}

Always ensure your response is valid JSON and includes all required fields.
Be precise and deterministic in your analysis.""",
        description="System message for rules analysis"
    )
