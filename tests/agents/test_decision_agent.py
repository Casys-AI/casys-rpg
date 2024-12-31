"""Tests for the decision agent module."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agents import DecisionAgent, ModelFactory, GameFactory
from agents.protocols import DecisionAgentProtocol
from managers.protocols import DecisionManagerProtocol, RulesManagerProtocol

from models import (
    GameState, RulesModel, DiceType, Choice, ChoiceType,
    DecisionModel, CharacterModel, CharacterStats, DecisionError, StateError, Inventory, Item
)
from models.types.common_types import NextActionType
from models.trace_model import ActionType
from models.types.agent_types import GameAgents
from models.types.manager_types import GameManagers
from config.agents import DecisionAgentConfig

@pytest.fixture
def mock_decision_manager() -> DecisionManagerProtocol:
    """Create a mock decision manager."""
    manager = AsyncMock(spec=DecisionManagerProtocol)
    manager.validate_choice = AsyncMock(return_value=True)
    manager.process_decision = AsyncMock()
    manager.get_cached_decision = AsyncMock(return_value=None)
    manager.save_decision = AsyncMock()
    return manager

@pytest.fixture
def mock_rules_agent() -> RulesManagerProtocol:
    """Create a mock rules agent."""
    agent = AsyncMock(spec=RulesManagerProtocol)
    agent.process_rules = AsyncMock()
    return agent

@pytest.fixture
def model_factory() -> ModelFactory:
    """Create a model factory for testing."""
    return ModelFactory()

@pytest.fixture
def mock_game_managers(mock_decision_manager, mock_rules_agent) -> GameManagers:
    """Create mock game managers."""
    return GameManagers(
        state_manager=AsyncMock(),
        cache_manager=AsyncMock(),
        character_manager=AsyncMock(),
        trace_manager=AsyncMock(),
        rules_manager=mock_rules_agent,
        decision_manager=mock_decision_manager,
        narrator_manager=AsyncMock(),
        workflow_manager=AsyncMock()
    )

@pytest.fixture
def mock_game_agents(mock_rules_agent, decision_agent) -> GameAgents:
    """Create mock game agents."""
    return GameAgents(
        narrator_agent=AsyncMock(),
        rules_agent=mock_rules_agent,
        decision_agent=decision_agent,
        trace_agent=AsyncMock()
    )

@pytest.fixture
def game_factory(mock_game_managers, mock_game_agents) -> GameFactory:
    """Create a game factory for testing."""
    factory = GameFactory()
    # Mock the internal create methods to return our mocks
    factory._create_managers = lambda: {"decision_manager": mock_game_managers.decision_manager}
    factory._create_agents = lambda _: {"decision_agent": mock_game_agents.decision_agent}
    return factory

@pytest.fixture
def decision_config(mock_rules_agent) -> DecisionAgentConfig:
    """Create a test decision agent config."""
    config = DecisionAgentConfig()
    config.llm = AsyncMock()
    config.dependencies = {"rules_agent": mock_rules_agent}
    return config

@pytest_asyncio.fixture
async def decision_agent(decision_config, mock_decision_manager) -> DecisionAgentProtocol:
    """Create a test decision agent."""
    return DecisionAgent(
        config=decision_config,
        decision_manager=mock_decision_manager
    )

@pytest.fixture
def sample_character() -> CharacterModel:
    """Create a sample character for testing."""
    return CharacterModel(
        name="Test Character",
        stats=CharacterStats(
            endurance=20,
            chance=20,
            skill=20
        ),
        inventory=Inventory(
            items={"sword": Item(name="sword", quantity=1)}
        )
    )

@pytest.fixture
def sample_rules_model() -> RulesModel:
    """Create sample rules model."""
    return RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        needs_dice=False,
        needs_user_response=True,
        next_action=NextActionType.USER_FIRST,
        conditions=["SKILL > 8"],
        choices=[
            Choice(
                text="Fight the monster",
                type=ChoiceType.DIRECT,
                target_section=2
            )
        ],
        rules_summary="Test combat rules"
    )

@pytest.fixture
def sample_decision_model() -> DecisionModel:
    """Create sample decision model."""
    return DecisionModel(
        section_number=1,
        next_section=None,
        awaiting_action=ActionType.USER_INPUT,
        next_action=NextActionType.USER_FIRST,
        conditions=["SKILL > 8"]
    )

@pytest.fixture
def sample_game_state(model_factory, sample_character) -> GameState:
    """Create a sample game state."""
    return model_factory.create_game_state(
        game_id="test_game",
        session_id="test_session",
        section_number=1,
        character=sample_character,
        player_input="1"  # Choose combat
    )

@pytest.mark.asyncio
async def test_decision_agent_initialization(decision_agent):
    """Test decision agent initialization."""
    assert decision_agent.config is not None
    assert decision_agent.decision_manager is not None
    assert decision_agent.rules_agent is not None
    assert decision_agent.llm is not None

@pytest.mark.asyncio
async def test_process_decision_cache_hit(
    decision_agent, mock_decision_manager, sample_decision_model, sample_game_state
):
    """Test processing decision with cache hit."""
    # Setup cache hit
    mock_decision_manager.get_cached_decision.return_value = sample_decision_model
    
    # Process decision
    result = await decision_agent.process_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, DecisionModel)
    assert result.section_number == sample_game_state.section_number
    assert len(result.conditions) == 1
    
    # Verify cache usage
    mock_decision_manager.get_cached_decision.assert_called_once_with(1)
    mock_decision_manager.process_decision.assert_not_called()

@pytest.mark.asyncio
async def test_process_decision_cache_miss(
    decision_agent, mock_decision_manager, mock_rules_agent,
    sample_decision_model, sample_game_state, sample_rules_model
):
    """Test processing decision with cache miss."""
    # Setup cache miss
    mock_decision_manager.get_cached_decision.return_value = None
    mock_rules_agent.process_rules.return_value = sample_rules_model
    mock_decision_manager.process_decision.return_value = sample_decision_model
    
    # Process decision
    result = await decision_agent.process_decision(sample_game_state)
    
    # Verify result
    assert isinstance(result, DecisionModel)
    assert result.section_number == sample_game_state.section_number
    
    # Verify workflow
    mock_decision_manager.get_cached_decision.assert_called_once()
    mock_rules_agent.process_rules.assert_called_once()
    mock_decision_manager.process_decision.assert_called_once()

@pytest.mark.asyncio
async def test_validate_choice(
    decision_agent, mock_decision_manager,
    sample_decision_model, sample_game_state
):
    """Test choice validation."""
    # Test valid choice
    result = await decision_agent.validate_choice(
        sample_decision_model,
        "1",  # Combat choice
        sample_game_state
    )
    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    
    # Test invalid choice number
    with pytest.raises(ValueError):
        await decision_agent.validate_choice(
            sample_decision_model,
            "3",  # Invalid choice
            sample_game_state
        )
    
    # Test choice with unmet conditions
    character_no_skill = sample_game_state.model_copy()
    character_no_skill.character.stats.SKILL = 5
    result = await decision_agent.validate_choice(
        sample_decision_model,
        "2",  # Stealth choice
        character_no_skill
    )
    assert result.is_valid is False

@pytest.mark.asyncio
async def test_process_decision_error(
    decision_agent, mock_decision_manager, sample_game_state
):
    """Test decision processing with error."""
    # Setup error case
    error = DecisionError(section_number=1, message="Invalid decision")
    mock_decision_manager.process_decision.side_effect = Exception("Processing error")
    
    # Process decision
    with pytest.raises(DecisionError):
        await decision_agent.process_decision(sample_game_state)

@pytest.mark.asyncio
async def test_analyze_response(
    decision_agent, mock_decision_manager,
    sample_decision_model, sample_game_state
):
    """Test response analysis."""
    # Setup analysis
    mock_decision_manager.analyze_response.return_value = AnalysisResult(
        is_valid=True,
        next_section=145,
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT
    )
    
    # Analyze response
    result = await decision_agent.analyze_response(
        sample_game_state.section_number,
        sample_game_state.player_input,
        sample_decision_model
    )
    
    # Verify analysis
    assert isinstance(result, AnalysisResult)
    assert result.is_valid is True
    assert result.next_section == 145
    assert result.needs_dice_roll is True
    assert result.dice_type == DiceType.COMBAT

@pytest.mark.asyncio
async def test_process_invalid_state(decision_agent, sample_game_state):
    """Test processing with invalid state."""
    # Create invalid state
    invalid_state = sample_game_state.model_copy()
    invalid_state.section_number = -1
    
    # Process invalid state
    with pytest.raises(ValueError):
        await decision_agent.process_decision(invalid_state)

@pytest.mark.asyncio
async def test_process_dice_decision(
    decision_agent, mock_decision_manager,
    sample_decision_model, sample_game_state
):
    """Test processing dice-based decision."""
    # Setup dice decision
    dice_model = sample_decision_model.model_copy()
    dice_model.decision_type = DecisionType.DICE
    dice_model.dice_type = DiceType.COMBAT
    mock_decision_manager.get_cached_decision.return_value = dice_model
    
    # Process decision
    result = await decision_agent.process_decision(sample_game_state)
    
    # Verify dice handling
    assert isinstance(result, DecisionModel)
    assert result.decision_type == DecisionType.DICE
    assert result.dice_type == DiceType.COMBAT
