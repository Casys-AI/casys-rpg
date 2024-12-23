"""Agent configuration model module."""
from pydantic import BaseModel, Field

from config.agents.agent_config_base import AgentConfigBase

class AgentConfigModel(BaseModel):
    """Configuration model for agent validation."""
    config: AgentConfigBase = Field(..., description="Base configuration for the agent")
