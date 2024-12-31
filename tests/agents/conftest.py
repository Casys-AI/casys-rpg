"""Agent-specific test fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from models.narrator_model import NarratorModel, SourceType
from models.game_state import GameState
from config.agents.narrator_agent_config import NarratorAgentConfig
from managers.protocols.narrator_manager_protocol import NarratorManagerProtocol

# Agent Configurations

@pytest.fixture
def narrator_agent_config():
    """Create a narrator agent configuration."""
    return NarratorAgentConfig(
        name="test_narrator",
        model_name="gpt-4o-mini",
        temperature=0.7,
        max_tokens=150
    )

# Agent Manager Mocks

@pytest.fixture
def mock_narrator_manager():
    """Create a mock narrator manager."""
    manager = AsyncMock(spec=NarratorManagerProtocol)
    manager.get_cached_content = AsyncMock(return_value=None)
    manager.get_raw_content = AsyncMock(return_value="Sample raw content")
    manager.format_content = MagicMock(return_value="Sample formatted content")
    manager.save_content = AsyncMock(return_value=NarratorModel(
        section_number=1,
        content="Sample formatted content",
        source_type=SourceType.PROCESSED
    ))
    return manager
