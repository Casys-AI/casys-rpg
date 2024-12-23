"""Tests for the rules agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from agents.rules_agent import RulesAgent
from models.rules_model import (
    RulesModel, DiceType, Choice, ChoiceType
)
from config.agents.rules_agent_config import RulesAgentConfig
from models.errors_model import RulesError

@pytest.fixture
def mock_rules_manager():
    """Create a mock rules manager."""
    manager = AsyncMock()
    # Configure the mock to return properly
    manager.get_section_rules = AsyncMock()
    manager.analyze_rules = AsyncMock()
    return manager

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = AsyncMock()
    llm.apredict = AsyncMock(return_value='{"result": "success"}')
    return llm

@pytest.fixture
def config(mock_llm):
    """Create a test rules agent config."""
    config = RulesAgentConfig()
    config.llm = mock_llm
    return config

@pytest.fixture
def rules_agent(config, mock_rules_manager):
    """Create a test rules agent."""
    return RulesAgent(config, mock_rules_manager)

@pytest.fixture
def sample_rules_content():
    """Sample rules content for testing."""
    return """
    # Section 1
    
    ## Rules
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
        needs_dice=True,  # Changed from needs_dice_roll
        dice_type=DiceType.COMBAT,
        conditions=["Must have sword", "SKILL > 8"],
        choices=[
            Choice(
                text="Combat with troll",
                type=ChoiceType.DICE,
                dice_type=DiceType.COMBAT,
                dice_results={"success": 145, "failure": 278}
            ),
            Choice(
                text="Try stealth",
                type=ChoiceType.MIXED,
                conditions=["SKILL > 8"],
                dice_type=DiceType.CHANCE,
                dice_results={"success": 145, "failure": 278}
            )
        ],
        rules_summary="Combat with troll and stealth check required"
    )

@pytest.mark.asyncio
async def test_process_section_rules_cache_hit(rules_agent, mock_rules_manager, sample_rules_model):
    """Test processing rules with cache hit."""
    # Setup mock to return our model
    mock_rules_manager.get_section_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify the result
    assert result.section_number == sample_rules_model.section_number
    assert result.needs_dice == sample_rules_model.needs_dice  # Changed from needs_dice_roll
    assert result.dice_type == sample_rules_model.dice_type
    assert result.conditions == sample_rules_model.conditions
    assert len(result.choices) == len(sample_rules_model.choices)
    assert result.rules_summary == sample_rules_model.rules_summary
    
    # Verify the mock was called correctly
    mock_rules_manager.get_section_rules.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_process_section_rules_cache_miss(
    rules_agent, mock_rules_manager, mock_llm, sample_rules_content, sample_rules_model
):
    """Test processing rules with cache miss."""
    # Setup mocks
    mock_rules_manager.get_section_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = sample_rules_content
    mock_llm.apredict.return_value = sample_rules_model.model_dump_json()
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice
    assert result.dice_type == DiceType.COMBAT
    
    # Verify manager calls
    mock_rules_manager.get_section_rules.assert_called_once_with(1)
    mock_rules_manager.get_raw_rules.assert_called_once_with(1)
    mock_rules_manager.analyze_rules.assert_called_once()

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
    mock_llm.apredict.side_effect = Exception("LLM error")
    
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
    mock_llm.apredict.return_value = sample_rules_model.model_dump_json()
    
    # Process rules with content
    result = await rules_agent.process_section_rules(1, content="Test rules content")
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice == sample_rules_model.needs_dice
    assert result.dice_type == sample_rules_model.dice_type
    
    # Verify manager calls
    mock_rules_manager.get_section_rules.assert_not_called()
    mock_rules_manager.get_raw_rules.assert_not_called()
    mock_rules_manager.analyze_rules.assert_called_once()
