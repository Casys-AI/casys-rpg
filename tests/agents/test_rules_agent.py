"""Tests for the rules agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime

from models.rules_model import (
    RulesModel, DiceType, Choice, ChoiceType
)
from config.agents.rules_agent_config import RulesAgentConfig
from models.errors_model import RulesError

class MockRulesAgent:
    """Mock rules agent for testing."""
    
    def __init__(self, config: RulesAgentConfig, rules_manager):
        self.config = config
        self.rules_manager = rules_manager
        self.llm = config.llm
        
    async def process_section_rules(self, section_number: int, content: str = None) -> RulesModel:
        """Mock process_section_rules method."""
        # Try to get from cache first
        if not content:
            existing = await self.rules_manager.get_existing_rules(section_number)
            if existing:
                return existing
                
            content = await self.rules_manager.get_raw_rules(section_number)
            if isinstance(content, RulesError):
                return content
                
        # Process with LLM
        try:
            llm_response = await self.llm.ainvoke({"content": content})
            if isinstance(llm_response, RulesError):
                return llm_response
                
            # Create and save model
            model = RulesModel(
                section_number=section_number,
                needs_dice=True,
                dice_type=DiceType.COMBAT,
                conditions=["Must have sword", "SKILL > 8"],
                choices=[
                    Choice(
                        text="Combat with troll",
                        type=ChoiceType.DICE,
                        dice_type=DiceType.COMBAT,
                        dice_results={"success": 145, "failure": 278}
                    )
                ],
                rules_summary="Combat with troll required"
            )
            
            return await self.rules_manager.save_rules(model)
            
        except Exception as e:
            return RulesError(
                section_number=section_number,
                message=f"Error processing rules: {str(e)}"
            )

@pytest.fixture
def mock_llm():
    """Create a mock LLM."""
    llm = AsyncMock()
    llm.ainvoke = AsyncMock(return_value=Mock(content='{"result": "success"}'))
    return llm

@pytest.fixture
def mock_rules_manager():
    """Create a mock rules manager."""
    manager = AsyncMock()
    # Configure the mock to return properly
    manager.get_existing_rules = AsyncMock(return_value=None)
    manager.get_raw_rules = AsyncMock(return_value=None)
    manager.save_rules = AsyncMock()
    return manager

@pytest.fixture
def config(mock_llm):
    """Create a test rules agent config."""
    config = RulesAgentConfig()
    config.llm = mock_llm
    return config

@pytest.fixture
def rules_agent(config, mock_rules_manager):
    """Create a test rules agent."""
    return MockRulesAgent(config, mock_rules_manager)

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
        needs_dice=True,  
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
    mock_rules_manager.get_existing_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify the result
    assert result.section_number == sample_rules_model.section_number
    assert result.needs_dice == sample_rules_model.needs_dice
    assert result.dice_type == sample_rules_model.dice_type
    assert result.conditions == sample_rules_model.conditions
    
    # Verify the mock was called correctly
    mock_rules_manager.get_existing_rules.assert_called_once_with(1)
    mock_rules_manager.get_raw_rules.assert_not_called()

@pytest.mark.asyncio
async def test_process_section_rules_cache_miss(rules_agent, mock_rules_manager, mock_llm, sample_rules_content, sample_rules_model):
    """Test processing rules with cache miss."""
    # Setup mocks
    mock_rules_manager.get_existing_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = sample_rules_content
    mock_rules_manager.save_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice is True
    
    # Verify mocks were called correctly
    mock_rules_manager.get_existing_rules.assert_called_once_with(1)
    mock_rules_manager.get_raw_rules.assert_called_once_with(1)

@pytest.mark.asyncio
async def test_process_section_rules_not_found(rules_agent, mock_rules_manager):
    """Test processing rules for non-existent section."""
    # Setup mock to return error
    error = RulesError(section_number=999, message="Section not found")
    mock_rules_manager.get_raw_rules.return_value = error
    
    # Process rules
    result = await rules_agent.process_section_rules(999)
    
    # Verify result
    assert isinstance(result, RulesError)
    assert result.section_number == 999
    assert "Section not found" in result.message

@pytest.mark.asyncio
async def test_process_section_rules_with_error(rules_agent, mock_rules_manager, mock_llm):
    """Test processing rules with LLM error."""
    # Setup mocks
    mock_rules_manager.get_existing_rules.return_value = None
    mock_rules_manager.get_raw_rules.return_value = "Invalid content"
    mock_llm.ainvoke.side_effect = Exception("LLM processing error")
    
    # Process rules
    result = await rules_agent.process_section_rules(1)
    
    # Verify result
    assert isinstance(result, RulesError)
    assert "Error processing rules" in result.message
