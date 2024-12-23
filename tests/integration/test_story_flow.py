"""Integration tests for the story flow."""
import pytest
import pytest_asyncio
from datetime import datetime
import shutil
import os

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from models.game_state import GameState
from models.character_model import CharacterModel, CharacterStats, Inventory, Item
from models.rules_model import DiceType
from models.errors_model import GameError

@pytest.fixture(scope="session", autouse=True)
def setup_teardown():
    """Setup and teardown for all tests."""
    # Setup
    os.makedirs("./test_data", exist_ok=True)
    
    yield
    
    # Teardown
    shutil.rmtree("./test_data", ignore_errors=True)

@pytest.fixture
def game_config():
    """Create a test game configuration."""
    config = GameConfig.create_default()
    # Update storage path for tests
    config.manager_configs.storage_config.base_path = "./test_data"
    return config

@pytest_asyncio.fixture
async def game_instance(game_config):
    """Create a test game instance."""
    factory = GameFactory(config=game_config)
    agents, managers = factory.create_game_components()
    await agents.story_graph.initialize()
    return agents.story_graph

@pytest.fixture
def sample_inventory():
    """Create a sample inventory."""
    inventory = Inventory()
    inventory.items["Sword"] = Item(name="Sword", description="A sharp sword")
    inventory.items["Shield"] = Item(name="Shield", description="A sturdy shield")
    inventory.gold = 10
    return inventory

@pytest.fixture
def sample_stats():
    """Create sample character stats."""
    return CharacterStats(
        health=20,
        max_health=20,
        strength=10,
        dexterity=10,
        intelligence=10,
        level=1,
        experience=0
    )

@pytest.fixture
def sample_character(sample_inventory, sample_stats):
    """Create a sample character."""
    return CharacterModel(
        stats=sample_stats,
        inventory=sample_inventory
    )

@pytest.mark.asyncio
async def test_game_initialization(game_instance):
    """Test game initialization."""
    assert game_instance is not None
    assert game_instance.current_state is not None
    assert game_instance.current_state.section_number == 0

@pytest.mark.asyncio
async def test_basic_story_progression(game_instance, sample_character):
    """Test basic story progression without combat."""
    # Create initial state
    state = GameState(
        section_number=1,
        player_input="go to section 2",
        character=sample_character,
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
async def test_combat_flow(game_instance, sample_character):
    """Test story progression with combat."""
    # Create combat state
    state = GameState(
        section_number=1,
        player_input="fight monster",
        character=sample_character,
        needs_dice_roll=True,
        dice_type=DiceType.COMBAT,
        last_update=datetime.now()
    )
    
    # Process combat turn
    result = await game_instance.process_turn(state)
    
    # Verify combat results
    assert isinstance(result, GameState)
    assert result.dice_rolls is not None
    assert result.character.stats.health != state.character.stats.health  # Combat should affect health

@pytest.mark.asyncio
async def test_invalid_choice(game_instance, sample_character):
    """Test handling of invalid choices."""
    # Create state with invalid choice
    state = GameState(
        section_number=1,
        player_input="invalid choice",
        character=sample_character,
        last_update=datetime.now()
    )
    
    # Process turn
    result = await game_instance.process_turn(state)
    
    # Verify error handling
    assert isinstance(result, GameState)
    assert result.error is not None
    assert "invalid choice" in result.error.lower()

@pytest.mark.asyncio
async def test_character_death(game_instance, sample_stats, sample_inventory):
    """Test handling of character death."""
    # Create dying character with 1 health
    dying_stats = CharacterStats(
        health=1,
        max_health=20,
        strength=10,
        dexterity=10,
        intelligence=10,
        level=1,
        experience=0
    )
    dying_character = CharacterModel(
        stats=dying_stats,
        inventory=sample_inventory
    )
    
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
    assert result.character.stats.health <= 0
    assert result.game_over

@pytest.mark.asyncio
async def test_game_save_load(game_instance, sample_character):
    """Test game state persistence."""
    # Create initial state
    initial_state = GameState(
        section_number=1,
        player_input="save game",
        character=sample_character,
        last_update=datetime.now()
    )
    
    # Save game
    save_result = await game_instance.save_game(initial_state)
    assert save_result
    
    # Load game
    loaded_state = await game_instance.load_game()
    assert loaded_state is not None
    assert loaded_state.section_number == initial_state.section_number
    assert loaded_state.character.stats.health == initial_state.character.stats.health

@pytest.mark.asyncio
async def test_full_story_sequence(game_instance, sample_character):
    """Test a complete story sequence."""
    # Initial state
    state = GameState(
        section_number=1,
        player_input="start adventure",
        character=sample_character,
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
