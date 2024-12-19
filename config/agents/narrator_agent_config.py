"""Narrator Agent configuration."""
from pydantic import Field
from config.agents.agent_config_base import AgentConfigBase
from config.game_constants import ModelType

class NarratorAgentConfig(AgentConfigBase):
    """Configuration specific to NarratorAgent."""
    model_name: str = Field(
        default=ModelType.NARRATOR,
        description="Model for narrative generation"
    )
    system_message: str = Field(
        default="""You are a skilled narrator for an interactive game book.
Your role is to format the content in clean Markdown, ensuring:
1. Section titles are properly formatted with '#'
2. Choices and links are properly formatted with [[]]
3. Preserve all game mechanics mentions (dice rolls, stats, etc.)
4. Keep the original text meaning intact
5. Format paragraphs for better readability""",
        description="System message for narrator"
    )
