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

Your task is to process and format game sections into engaging narrative content.
You must format the content in the following way:

# Section [X]

[Content of the section in markdown format]

Format guidelines:
1. Start with "# Section" followed by the section number
2. Add a blank line after the title
3. Format the content in clean Markdown
4. Choices numbers should be formatted with [[]] e.g. [[1]] [[398]]
5. Preserve all game mechanics mentions (dice rolls, stats, etc.)
6. Keep the original text meaning intact
7. Format paragraphs for better readability

Example:
# Section 1

You stand at the entrance of a dark cave. The wind howls ominously, and you can barely make out two paths ahead:

- To the left, a narrow passage seems to lead downward [[145]]
- To the right, a wider tunnel continues straight ahead [[278]]

Roll 2d6 to check your SKILL score before proceeding.""",
        description="System message for narrator"
    )
