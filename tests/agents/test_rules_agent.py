"""Tests for the rules agent module."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from agents import RulesAgent, ModelFactory, GameFactory
from agents.protocols import RulesAgentProtocol
from managers.protocols import RulesManagerProtocol, CacheManagerProtocol

from models import (
    GameState, RulesModel, DiceType, Choice, ChoiceType,
    CharacterModel, CharacterStats, RulesError
)
from config.agents import RulesAgentConfig
from config.game_config import GameConfig

@pytest.fixture
def mock_rules_manager() -> RulesManagerProtocol:
    """Create a mock rules manager."""
    manager = AsyncMock(spec=RulesManagerProtocol)
    manager.get_cached_rules = AsyncMock(return_value=None)
    manager.process_rules = AsyncMock()
    manager.save_rules = AsyncMock()
    manager.validate_rules = AsyncMock(return_value=True)
    return manager

@pytest.fixture
def mock_cache_manager() -> CacheManagerProtocol:
    """Create a mock cache manager."""
    manager = AsyncMock(spec=CacheManagerProtocol)
    manager.get_cached_data = AsyncMock(return_value=None)
    manager.save_to_cache = AsyncMock()
    return manager

@pytest.fixture
def model_factory() -> ModelFactory:
    """Create a model factory for testing."""
    return ModelFactory()

@pytest.fixture
def game_factory(mock_rules_manager, mock_cache_manager) -> GameFactory:
    """Create a game factory for testing."""
    config = GameConfig()
    config.manager_configs.rules_config = mock_rules_manager
    config.manager_configs.cache_config = mock_cache_manager
    return GameFactory(config=config)

@pytest.fixture
def rules_config() -> RulesAgentConfig:
    """Create a test rules agent config."""
    config = RulesAgentConfig()
    config.llm = AsyncMock()
    config.system_message = "Test system message"
    return config

@pytest_asyncio.fixture
async def rules_agent(rules_config, mock_rules_manager) -> RulesAgentProtocol:
    """Create a test rules agent."""
    return RulesAgent(
        config=rules_config,
        rules_manager=mock_rules_manager
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
def sample_rules_model() -> RulesModel:
    """Create sample rules model."""
    return RulesModel(
        section_number=1,
        needs_dice=True,
        dice_type=DiceType.COMBAT,
        conditions=[
            "Must have sword",
            "SKILL > 8"
        ],
        choices=[
            Choice(
                text="Combat with troll",
                type=ChoiceType.DICE,
                dice_type=DiceType.COMBAT,
                dice_results={"success": 145, "failure": 278}
            ),
            Choice(
                text="Try stealth",
                type=ChoiceType.CONDITIONAL,
                conditions=["SKILL > 8"],
                target_section=145
            )
        ],
        next_action=NextActionType.USER_FIRST,
        needs_user_response=True
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
async def test_rules_agent_initialization(rules_agent):
    """Test rules agent initialization."""
    assert rules_agent is not None
    assert rules_agent.config is not None
    assert rules_agent.config.llm is not None
    assert rules_agent.rules_manager is not None

@pytest.mark.asyncio
async def test_process_rules_cache_hit(
    rules_agent, mock_rules_manager, sample_rules_model, sample_game_state
):
    """Test processing rules with cache hit."""
    # Setup cache hit
    mock_rules_manager.get_cached_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_rules(sample_game_state)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == sample_game_state.section_number
    assert len(result.choices) == 2
    
    # Verify cache usage
    mock_rules_manager.get_cached_rules.assert_called_once_with(1)
    mock_rules_manager.process_rules.assert_not_called()

@pytest.mark.asyncio
async def test_process_rules_cache_miss(
    rules_agent, mock_rules_manager, sample_rules_model, sample_game_state
):
    """Test processing rules with cache miss."""
    # Setup cache miss
    mock_rules_manager.get_cached_rules.return_value = None
    mock_rules_manager.process_rules.return_value = sample_rules_model
    
    # Process rules
    result = await rules_agent.process_rules(sample_game_state)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == sample_game_state.section_number
    
    # Verify workflow
    mock_rules_manager.get_cached_rules.assert_called_once()
    mock_rules_manager.process_rules.assert_called_once()

@pytest.mark.asyncio
async def test_validate_conditions(
    rules_agent, mock_rules_manager, sample_rules_model, sample_game_state
):
    """Test condition validation."""
    # Test valid conditions
    result = await rules_agent.validate_conditions(
        sample_rules_model.conditions,
        sample_game_state
    )
    assert isinstance(result, ValidationResult)
    assert result.is_valid is True
    
    # Test invalid conditions (missing item)
    character_no_sword = sample_game_state.model_copy()
    character_no_sword.character.inventory.remove("sword")
    result = await rules_agent.validate_conditions(
        sample_rules_model.conditions,
        character_no_sword
    )
    assert result.is_valid is False
    
    # Test invalid conditions (low skill)
    character_low_skill = sample_game_state.model_copy()
    character_low_skill.character.stats.SKILL = 5
    result = await rules_agent.validate_conditions(
        sample_rules_model.conditions,
        character_low_skill
    )
    assert result.is_valid is False

@pytest.mark.asyncio
async def test_process_dice_roll(
    rules_agent, mock_rules_manager, sample_rules_model, sample_game_state
):
    """Test dice roll processing."""
    # Setup dice roll
    mock_rules_manager.process_dice_roll.return_value = (True, 12)
    
    # Process dice roll
    result = await rules_agent.process_dice_roll(
        dice_type=DiceType.COMBAT,
        character=sample_game_state.character
    )
    
    # Verify dice roll
    assert isinstance(result, tuple)
    assert result[0] is True  # Success
    assert result[1] == 12  # Roll value

@pytest.mark.asyncio
async def test_process_skill_check(
    rules_agent, mock_rules_manager, sample_rules_model, sample_game_state
):
    """Test skill check processing."""
    skill_check = {"stat": "SKILL", "value": 8, "operator": ">"}
    
    # Test successful skill check
    result = await rules_agent.process_skill_check(
        skill_check=skill_check,
        character=sample_game_state.character
    )
    assert result is True
    
    # Test failed skill check
    character_low_skill = sample_game_state.model_copy()
    character_low_skill.character.stats.SKILL = 5
    result = await rules_agent.process_skill_check(
        skill_check=skill_check,
        character=character_low_skill.character
    )
    assert result is False

@pytest.mark.asyncio
async def test_process_invalid_state(rules_agent, sample_game_state):
    """Test processing with invalid state."""
    # Create invalid state
    invalid_state = sample_game_state.model_copy()
    invalid_state.section_number = -1
    
    # Process invalid state
    with pytest.raises(ValueError):
        await rules_agent.process_rules(invalid_state)

@pytest.mark.asyncio
async def test_process_rules_error(
    rules_agent, mock_rules_manager, sample_game_state
):
    """Test rules processing with error."""
    # Setup error case
    mock_rules_manager.process_rules.side_effect = Exception("Processing error")
    
    # Process rules
    with pytest.raises(RulesError):
        await rules_agent.process_rules(sample_game_state)
