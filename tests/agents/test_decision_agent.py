"""Tests for the decision agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from agents.decision_agent import DecisionAgent
from agents.factories.game_factory import GameFactory
from config.agents.decision_agent_config import DecisionAgentConfig
from config.agents.narrator_agent_config import NarratorAgentConfig
from config.agents.rules_agent_config import RulesAgentConfig
from config.agents.trace_agent_config import TraceAgentConfig
from config.game_config import GameConfig, ManagerConfigs, AgentConfigs
from config.storage_config import StorageConfig
from models.game_state import GameState
from models.rules_model import RulesModel, DiceType
from models.errors_model import DecisionError

@pytest.fixture
def mock_decision_manager():
    """Create a mock decision manager."""
    manager = Mock()
    manager.validate_choice = AsyncMock()
    manager.process_decision = AsyncMock()
    return manager

@pytest.fixture
def mock_rules_agent():
    """Create a mock rules agent."""
    agent = Mock()
    agent.process_section_rules = AsyncMock()
    return agent

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm

@pytest.fixture
def config(mock_llm, mock_rules_agent):
    """Create a test decision agent config."""
    return DecisionAgentConfig(
        llm=mock_llm,
        system_message="Test system message",
        dependencies={"rules_agent": mock_rules_agent}
    )

@pytest_asyncio.fixture
async def decision_agent(config, mock_decision_manager, mock_llm):
    """Create a test decision agent."""
    # Create test game config
    game_config = GameConfig(
        manager_configs=ManagerConfigs(
            storage_config=StorageConfig(base_path="./test_data")
        ),
        agent_configs=AgentConfigs(
            narrator_config=NarratorAgentConfig(llm=mock_llm),
            rules_config=RulesAgentConfig(llm=mock_llm),
            decision_config=config,
            trace_config=TraceAgentConfig(llm=mock_llm)
        )
    )
    
    # Create factory with test config
    factory = GameFactory(game_config)
    
    # Create all components
    agents, managers = factory.create_game_components()
    
    # Replace managers with mocks
    agents.decision_agent = DecisionAgent(config=config, decision_manager=mock_decision_manager)
    
    return agents.decision_agent

@pytest.fixture
def sample_game_state():
    """Create a sample game state."""
    return GameState(
        section_number=1,
        player_input="go to [[145]]",
        last_update=datetime.now()
    )

@pytest.fixture
def sample_rules_model():
    """Create a sample rules model."""
    return RulesModel(
        section_number=1,
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT,
        conditions=["Must have sword", "SKILL > 8"],
        next_sections=[145, 278],
        rules_summary="Combat with troll required"
    )

@pytest.mark.asyncio
async def test_analyze_decision_valid_choice(
    decision_agent, mock_decision_manager, mock_rules_agent,
    sample_game_state, sample_rules_model
):
    """Test analyzing a valid decision."""
    # Setup mocks
    mock_rules_agent.process_section_rules.return_value = sample_rules_model
    mock_decision_manager.validate_choice.return_value = True
    
    # Analyze decision
    result = await decision_agent.analyze_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.section_number == 1
    assert not result.error
    
    # Verify manager calls
    mock_rules_agent.process_section_rules.assert_called_once_with(1)
    mock_decision_manager.validate_choice.assert_called_once()

@pytest.mark.asyncio
async def test_analyze_decision_invalid_choice(
    decision_agent, mock_decision_manager, mock_rules_agent,
    sample_game_state, sample_rules_model
):
    """Test analyzing an invalid decision."""
    # Setup mocks
    mock_rules_agent.process_section_rules.return_value = sample_rules_model
    mock_decision_manager.validate_choice.return_value = False
    
    # Analyze decision
    result = await decision_agent.analyze_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.error
    assert "invalid choice" in result.error.lower()

@pytest.mark.asyncio
async def test_analyze_decision_rules_error(
    decision_agent, mock_decision_manager, mock_rules_agent,
    sample_game_state
):
    """Test analyzing decision with rules error."""
    # Setup mock
    mock_rules_agent.process_section_rules.side_effect = Exception("Rules error")
    
    # Analyze decision
    result = await decision_agent.analyze_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.error
    assert "rules error" in result.error.lower()

@pytest.mark.asyncio
async def test_validate_choice(decision_agent):
    """Test choice validation."""
    # Test valid choice
    valid = await decision_agent.validate_choice("145", ["145", "278"])
    assert valid
    
    # Test invalid choice
    valid = await decision_agent.validate_choice("999", ["145", "278"])
    assert not valid

@pytest.mark.asyncio
async def test_analyze_decision_with_dice_roll(
    decision_agent, mock_decision_manager, mock_rules_agent,
    sample_game_state, sample_rules_model
):
    """Test analyzing decision requiring dice roll."""
    # Setup mocks
    mock_rules_agent.process_section_rules.return_value = sample_rules_model
    mock_decision_manager.validate_choice.return_value = True
    
    # Analyze decision
    result = await decision_agent.analyze_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, GameState)
    assert result.needs_dice_roll
    assert result.dice_type == DiceType.COMBAT
