# config/agents/agent_config_base.py
"""Base configuration for all agents."""
from typing import Optional, Dict, Any, ClassVar
from pydantic import Field
from functools import cached_property
import os
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from models.config_models import ConfigModel
from config.game_constants import ModelType, DEFAULT_TEMPERATURE
from config.logging_config import get_logger

class AgentConfigBase(ConfigModel):
    """Base configuration for all agents."""
    model_name: str = Field(
        default=os.getenv("LLM_MODEL_NAME", ModelType.NARRATOR),
        description="Name of the language model"
    )
    temperature: float = Field(
        default=float(os.getenv("LLM_TEMPERATURE", str(DEFAULT_TEMPERATURE))),
        description="Temperature for LLM responses"
    )
    system_message: str = Field(
        default="",
        description="System message for LLM"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens for response"
    )
    custom_parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional model parameters"
    )
    dependencies: Dict[str, Any] = Field(
        default_factory=dict,
        description="Agent dependencies"
    )

    @cached_property
    def llm(self) -> BaseChatModel:
        """Create and return LLM instance."""
        return ChatOpenAI(
            model=self.model_name,
            temperature=self.temperature
        )

    def setup_logging(self, logger_name: str) -> None:
        """Configure logging for the agent."""
        get_logger(logger_name)
