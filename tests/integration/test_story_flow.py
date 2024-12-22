"""Integration tests for the story flow."""
import pytest
import pytest_asyncio
from datetime import datetime

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from models.game_state import GameState
from models.character_model import CharacterModel
from models.rules_model import DiceType
from models.errors_model import GameError

@pytest.fixture
def game_config():
    """Create a test game configuration."""
    return GameConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def game_instance(game_config):
    """Create a test game instance."""
    factory = GameFactory(config=game_config)
    game = factory.create_game()
    await game.initialize()
    return game

@pytest.fixture
def sample_character():
    """Create a sample character."""
    return CharacterModel(
        name="Test Hero",
        skill=10,
        stamina=20,
        luck=7,
        inventory=["Sword", "Shield"],
        gold=10
    )

@pytest.mark.asyncio
async def test_game_initialization(game_instance):
    """Test game initialization."""
    assert game_instance.story_graph is not None
    assert game_instance.current_state is not None
    assert game_instance.current_state.section_number == 0

@pytest.mark.asyncio
async def test_basic_story_progression(game_instance):
    """Test basic story progression without combat."""
    # Create initial state
    state = GameState(
        section_number=1,
        player_input="go to section 2",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # Process turn
    result = await game_instance.process_turn(state)
    
    # Verify progression
    assert isinstance(result, GameState)
    assert not result.error
    assert result.section_number in [1, 2]  # Depends on rules
    assert result.character is not None

@pytest.mark.asyncio
async def test_combat_flow(game_instance):
    """Test story progression with combat."""
    # Create combat state
    state = GameState(
        section_number=1,
        player_input="fight monster",
        character=sample_character(),
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT,
        last_update=datetime.now()
    )
    
    # Process combat turn
    result = await game_instance.process_turn(state)
    
    # Verify combat results
    assert isinstance(result, GameState)
    assert result.dice_rolls is not None
    assert result.character.stamina != state.character.stamina  # Combat should affect stamina

@pytest.mark.asyncio
async def test_invalid_choice(game_instance):
    """Test handling of invalid choices."""
    # Create state with invalid choice
    state = GameState(
        section_number=1,
        player_input="invalid choice",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # Process turn
    result = await game_instance.process_turn(state)
    
    # Verify error handling
    assert isinstance(result, GameState)
    assert result.error is not None
    assert "invalid choice" in result.error.lower()

@pytest.mark.asyncio
async def test_character_death(game_instance):
    """Test handling of character death."""
    # Create dying character
    dying_character = sample_character()
    dying_character.stamina = 1
    
    state = GameState(
        section_number=1,
        player_input="fight monster",
        character=dying_character,
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT,
        last_update=datetime.now()
    )
    
    # Process turn
    result = await game_instance.process_turn(state)
    
    # Verify death handling
    assert isinstance(result, GameState)
    assert result.character.stamina <= 0
    assert result.game_over

@pytest.mark.asyncio
async def test_game_save_load(game_instance):
    """Test game state persistence."""
    # Create initial state
    initial_state = GameState(
        section_number=1,
        player_input="save game",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # Save game
    save_result = await game_instance.save_game(initial_state)
    assert save_result
    
    # Load game
    loaded_state = await game_instance.load_game()
    assert loaded_state is not None
    assert loaded_state.section_number == initial_state.section_number
    assert loaded_state.character.name == initial_state.character.name

@pytest.mark.asyncio
async def test_full_story_sequence(game_instance):
    """Test a complete story sequence."""
    # Initial state
    state = GameState(
        section_number=1,
        player_input="start adventure",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # Process multiple turns
    for _ in range(5):  # Test 5 turns
        if state.error or state.game_over:
            break
            
        # Process turn
        state = await game_instance.process_turn(state)
        
        # Verify state
        assert isinstance(state, GameState)
        assert state.section_number > 0
        assert state.character is not None
        
        # Prepare next input based on current state
        if state.needs_dice_roll:
            state.player_input = "roll dice"
        else:
            state.player_input = "continue"
            
    # Verify story progression
    assert state.section_number != 1  # Story should have progressed
