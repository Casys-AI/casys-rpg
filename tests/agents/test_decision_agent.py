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
    DecisionModel, CharacterModel, CharacterStats, DecisionError, StateError
)
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
def game_factory(mock_decision_manager, mock_rules_agent) -> GameFactory:
    """Create a game factory for testing."""
    return GameFactory(
        decision_manager=mock_decision_manager,
        rules_agent=mock_rules_agent
    )

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
def sample_character(model_factory) -> CharacterModel:
    """Create a sample character for testing."""
    return model_factory.create_character(
        name="Test Character",
        stats=CharacterStats(SKILL=10, STAMINA=20, LUCK=5),
        inventory=["sword", "potion"]
    )

@pytest.fixture
def sample_rules_model(model_factory) -> RulesModel:
    """Create sample rules model."""
    return model_factory.create_rules_model(
        section_number=1,
        needs_dice=True,
        dice_type=DiceType.COMBAT,
        conditions=[
            RuleCondition(text="Must have sword", item_required="sword"),
            RuleCondition(text="SKILL > 8", stat_check={"stat": "SKILL", "value": 8, "operator": ">"})
        ],
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

@pytest.fixture
def sample_decision_model(model_factory) -> DecisionModel:
    """Create sample decision model."""
    return model_factory.create_decision_model(
        section_number=1,
        decision_type=DecisionType.CHOICE,
        choices={"1": "Combat with troll", "2": "Try stealth"},
        validation=ChoiceValidation(
            valid_choices=["1", "2"],
            conditions={"2": ["SKILL > 8"]}
        )
    )

@pytest.fixture
def sample_game_state(game_factory, sample_character) -> GameState:
    """Create a sample game state."""
    return game_factory.create_game_state(
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
    assert len(result.choices) == 2
    
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
