"""Trace Agent configuration."""
from typing import Dict, Any
from pydantic import Field
from config.agents.agent_config_base import AgentConfigBase
from config.game_constants import ModelType

class TraceAgentConfig(AgentConfigBase):
    """Configuration specific to TraceAgent."""
    
    # Trace detail level
    detail_level: str = Field(
        default="normal",
        description="Level of trace detail (minimal, normal, verbose)"
    )
    
    # Model settings
    model_name: str = Field(
        default=ModelType.TRACE,
        description="Model for trace analysis"
    )
    temperature: float = Field(
        default=0.0,  # Deterministic for tracing
        description="Temperature for trace analysis"
    )
    
    # Storage settings
    persist_trace: bool = Field(
        default=True,
        description="Persist trace data to storage"
    )
    compression_enabled: bool = Field(
        default=True,
        description="Compress trace data"
    )
    trace_dir: str = Field(
        default="data/trace",
        description="Directory for storing trace data"
    )
    
    # History settings
    max_history: int = Field(
        default=100,
        description="Maximum number of trace entries to keep"
    )
    cleanup_interval: int = Field(
        default=1000,
        description="Clean up interval in number of entries"
    )
