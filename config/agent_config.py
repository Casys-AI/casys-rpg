"""Configuration for different agent types."""
from typing import Optional, Dict, Any, ClassVar
from pydantic import Field
from functools import cached_property
import os
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
from config.core_config import CoreConfig
from config.constants import ModelType, DEFAULT_TEMPERATURE
from config.logging_config import get_logger

class AgentConfig(CoreConfig):
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

class NarratorConfig(AgentConfig):
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

class RulesConfig(AgentConfig):
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

class DecisionConfig(AgentConfig):
    """Configuration specific to DecisionAgent."""
    model_name: str = Field(
        default=ModelType.DECISION,
        description="Model for decision making"
    )
    temperature: float = Field(
        default=0.7,  # More creative for decisions
        description="Temperature for decision making"
    )

class TraceConfig(AgentConfig):
    """Configuration specific to TraceAgent."""
    model_name: str = Field(
        default=ModelType.TRACE,
        description="Model for trace analysis"
    )
    temperature: float = Field(
        default=0.0,  # Deterministic for tracing
        description="Temperature for trace analysis"
    )
    trace_dir: str = Field(
        default="data/trace",
        description="Directory for storing trace data"
    )
