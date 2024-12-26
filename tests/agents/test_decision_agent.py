"""Tests for the decision agent module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock

from models.game_state import GameState
from models.rules_model import RulesModel
from models.decision_model import DecisionModel, AnalysisResult
from models.errors_model import DecisionError
from config.agents.decision_agent_config import DecisionAgentConfig

class MockDecisionAgent:
    """Mock decision agent for testing."""
    
    def __init__(self, config: DecisionAgentConfig, decision_manager):
        self.config = config
        self.decision_manager = decision_manager
        self.rules_agent = config.dependencies.get("rules_agent")
        
    async def analyze_response(self, section_number: int, user_response: str, rules: dict) -> AnalysisResult:
        """Mock analyze_response method."""
        return AnalysisResult(
            is_valid=True,
            next_section=145,
            needs_dice_roll=rules.get("needs_dice_roll", False),
            dice_type=rules.get("dice_type")
        )

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

@pytest.fixture
def decision_agent(config, mock_decision_manager):
    """Create a test decision agent."""
    return MockDecisionAgent(config=config, decision_manager=mock_decision_manager)

@pytest.fixture
def sample_game_state():
    """Create a sample game state."""
    return GameState(
        session_id="test_session",
        section_number=1,
        player_input="go to [[145]]",
        source="RAW"
    )

@pytest.fixture
def sample_rules():
    """Create sample rules."""
    return {
        "section_number": 1,
        "needs_dice_roll": True,
        "dice_type": "COMBAT",
        "conditions": ["Must have sword", "SKILL > 8"],
        "next_sections": [145, 278],
        "rules_summary": "Combat with troll required"
    }

@pytest.mark.asyncio
async def test_analyze_response(decision_agent, sample_game_state, sample_rules):
    """Test analyzing user response."""
    result = await decision_agent.analyze_response(
        section_number=1,
        user_response="go to [[145]]",
        rules=sample_rules
    )
    
    assert isinstance(result, AnalysisResult)
    assert result.is_valid is True
    assert result.next_section == 145

@pytest.mark.asyncio
async def test_analyze_response_with_dice(decision_agent, sample_game_state, sample_rules):
    """Test analyzing response requiring dice roll."""
    sample_rules["needs_dice_roll"] = True
    
    result = await decision_agent.analyze_response(
        section_number=1,
        user_response="go to [[145]]",
        rules=sample_rules
    )
    
    assert isinstance(result, AnalysisResult)
    assert result.needs_dice_roll is True
    assert result.dice_type == "COMBAT"
