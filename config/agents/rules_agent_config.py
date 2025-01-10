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
    "needs_dice": true|false,        # If the user MUST roll dice to proceed (MUST be false if dice_type is none)
    "dice_type": "none"|"chance"|"combat",  # Type of dice roll required (if any)
    "needs_user_response": true|false,  # If user needs to make a choice to proceed
    "next_action": "user_first"|"dice_first"|null,  # Order of actions
    "conditions": ["condition1", "condition2"],  # List of conditions that apply
    "choices": [
        {
            "text": "Choice description",
            "type": "direct"|"conditional"|"dice"|"mixed",
            "target_section": 123,  # Optional, section number this leads to
            "conditions": ["condition1"],  # Optional, list of required conditions
            "dice_type": "none"|"chance"|"combat",  # Optional, type of dice roll
            "dice_results": {"6": 1, "5-6": 2}  # Optional, mapping of results to sections
        }
    ],
    "rules_summary": "Brief summary of the rules"  # Summary of the section's rules
}

Always ensure:
1. Your response is valid JSON
2. All fields are present
3. dice_type is one of: "none", "chance", "combat"
4. choice.type is one of: "direct", "conditional", "dice", "mixed"
5. All section numbers are positive integers
6. dice_results uses string keys for ranges""",
        description="System message for rules analysis"
    )

