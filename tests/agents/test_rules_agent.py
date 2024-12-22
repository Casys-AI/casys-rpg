"""Tests for the rules agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from agents.rules_agent import RulesAgent
from config.agents.rules_agent_config import RulesAgentConfig
from models.rules_model import RulesModel, DiceType
from models.errors_model import RulesError

@pytest.fixture
def mock_rules_manager():
    """Create a mock rules manager."""
    manager = Mock()
    manager.get_section_rules = AsyncMock()
    manager.get_raw_rules = AsyncMock()
    manager.save_section_rules = AsyncMock()
    return manager

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock()
    return llm

@pytest.fixture
def config(mock_llm):
    """Create a test rules agent config."""
    return RulesAgentConfig(
        llm=mock_llm,
        system_message="Test system message"
    )

@pytest_asyncio.fixture
async def rules_agent(config, mock_rules_manager):
    """Create a test rules agent."""
    agent = RulesAgent(config=config, rules_manager=mock_rules_manager)
    return agent

@pytest.fixture
def sample_rules_content():
    """Sample rules content for testing."""
    return """
    # Rules for Section 1
    
    ## Conditions
    - Must have sword
    - SKILL > 8
    
    ## Actions
    - Combat with troll (2d6)
    - Stealth check (1d6)
    
    ## Next Sections
    - Success: [[145]]
    - Failure: [[278]]
    """

@pytest.fixture
def sample_rules_model():
    """Create a sample rules model."""
    return RulesModel(
        section_number=1,
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT,
        conditions=["Must have sword", "SKILL > 8"],
        next_sections=[145, 278],
        rules_summary="Combat with troll and stealth check required"
    )

@pytest.mark.asyncio
async def test_process_section_rules_cache_hit(rules_agent, mock_rules_manager, sample_rules_model):
    """Test processing rules with cache hit."""
    # Setup mock
    mock_rules_manager.get_section_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice_roll == sample_rules_model.needs_dice_roll
    assert result.dice_type == sample_rules_model.dice_type
    assert result.conditions == sample_rules_model.conditions
    assert result.next_sections == sample_rules_model.next_sections
    
    # Verify manager calls
    mock_rules_manager.get_section_rules.assert_called_once_with(1)
    mock_rules_manager.get_raw_rules.assert_not_called()

@pytest.mark.asyncio
async def test_process_section_rules_cache_miss(
    rules_agent, mock_rules_manager, mock_llm, sample_rules_content, sample_rules_model
):
    """Test processing rules with cache miss."""
    # Setup mocks
    mock_rules_manager.get_section_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = sample_rules_content
    mock_llm.ainvoke.return_value.content = sample_rules_model.model_dump_json()
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice_roll
    assert result.dice_type == DiceType.COMBAT
    
    # Verify manager calls
    mock_rules_manager.get_section_rules.assert_called_once_with(1)
    mock_rules_manager.get_raw_rules.assert_called_once_with(1)
    mock_rules_manager.save_section_rules.assert_called_once()

@pytest.mark.asyncio
async def test_process_section_rules_not_found(rules_agent, mock_rules_manager):
    """Test processing rules for non-existent section."""
    # Setup mock
    mock_rules_manager.get_section_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = None
    
    # Process rules
    result = await rules_agent.process_section_rules(999)
    
    # Verify result
    assert isinstance(result, RulesError)
    assert result.section_number == 999
    assert "not found" in result.message.lower()

@pytest.mark.asyncio
async def test_process_section_rules_with_error(rules_agent, mock_rules_manager, mock_llm):
    """Test processing rules with LLM error."""
    # Setup mocks
    mock_rules_manager.get_section_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = "Test rules"
    mock_llm.ainvoke.side_effect = Exception("LLM error")
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesError)
    assert result.section_number == 1
    assert "llm error" in result.message.lower()

@pytest.mark.asyncio
async def test_process_section_rules_with_content(
    rules_agent, mock_rules_manager, mock_llm, sample_rules_model
):
    """Test processing rules with provided content."""
    # Setup mock
    mock_llm.ainvoke.return_value.content = sample_rules_model.model_dump_json()
    
    # Process rules with content
    result = await rules_agent.process_section_rules(1, content="Test rules content")
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice_roll == sample_rules_model.needs_dice_roll
    assert result.dice_type == sample_rules_model.dice_type
    
    # Verify manager calls
    mock_rules_manager.get_section_rules.assert_not_called()
    mock_rules_manager.get_raw_rules.assert_not_called()
    mock_rules_manager.save_section_rules.assert_called_once()
