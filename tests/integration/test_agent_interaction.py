"""Integration tests for agent interactions."""
import pytest
import pytest_asyncio
from datetime import datetime
import shutil
import os

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from models.game_state import GameState
from models.character_model import CharacterModel, CharacterStats, Inventory, Item
from models.rules_model import RulesModel, DiceType, Choice, ChoiceType
from models.narrator_model import NarratorModel
from models.trace_model import TraceModel

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
async def agents(game_config):
    """Create test agents."""
    factory = GameFactory(config=game_config)
    agents, managers = factory.create_game_components()
    return {
        "narrator": agents.narrator_agent,
        "rules": agents.rules_agent,
        "decision": agents.decision_agent,
        "trace": agents.trace_agent
    }

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

@pytest.fixture
def sample_choices():
    """Create sample choices for testing."""
    return [
        Choice(
            text="Go to section 2",
            type=ChoiceType.DIRECT,
            target_section=2
        ),
        Choice(
            text="Go to section 3",
            type=ChoiceType.CONDITIONAL,
            target_section=3,
            conditions=["has_sword"]
        )
    ]

@pytest.mark.asyncio
async def test_narrator_rules_interaction(agents):
    """Test interaction between narrator and rules agents."""
    # Get section content
    narrator_result = await agents["narrator"].process_section(1)
    assert isinstance(narrator_result, NarratorModel)
    
    # Process rules for the same section
    rules_result = await agents["rules"].process_section_rules(1)
    assert isinstance(rules_result, RulesModel)
    
    # Verify consistency
    assert narrator_result.section_number == rules_result.section_number

@pytest.mark.asyncio
async def test_rules_decision_interaction(agents, sample_character, sample_choices):
    """Test interaction between rules and decision agents."""
    # Create game state with rules
    state = GameState(
        section_number=1,
        player_input="test choice",
        character=sample_character,
        last_update=datetime.now(),
        rules=RulesModel(
            section_number=1,
            choices=sample_choices,
            needs_dice=True,
            dice_type=DiceType.COMBAT
        )
    )
    
    # Make decision based on rules
    decision_result = await agents["decision"].analyze_decision(state)
    
    # Verify decision considers rules
    assert isinstance(decision_result, GameState)
    assert decision_result.rules.needs_dice == state.rules.needs_dice
    assert decision_result.rules.dice_type == state.rules.dice_type

@pytest.mark.asyncio
async def test_decision_trace_interaction(agents, sample_character):
    """Test interaction between decision and trace agents."""
    # Create game state
    state = GameState(
        section_number=1,
        player_input="test choice",
        character=sample_character,
        last_update=datetime.now()
    )
    
    # Make decision
    decision_result = await agents["decision"].analyze_decision(state)
    assert isinstance(decision_result, GameState)
    
    # Record trace
    trace_result = await agents["trace"].record_state(decision_result)
    assert trace_result is None  # Should succeed silently
    
    # Verify trace recording
    current_trace = await agents["trace"]._manager.get_current_trace()
    assert isinstance(current_trace, TraceModel)
    assert len(current_trace.history) > 0
    assert current_trace.history[-1].section == decision_result.section_number

@pytest.mark.asyncio
async def test_full_agent_chain(agents, sample_character):
    """Test complete chain of agent interactions."""
    # Initial state
    state = GameState(
        section_number=1,
        player_input="start game",
        character=sample_character,
        last_update=datetime.now()
    )
    
    # 1. Get section content
    narrator_result = await agents["narrator"].process_section(state.section_number)
    assert isinstance(narrator_result, NarratorModel)
    
    # 2. Get rules
    rules_result = await agents["rules"].process_section_rules(state.section_number)
    assert isinstance(rules_result, RulesModel)
    
    # 3. Update state with rules
    state.rules = rules_result
    
    # 4. Make decision
    decision_result = await agents["decision"].analyze_decision(state)
    assert isinstance(decision_result, GameState)
    
    # 5. Record trace
    trace_result = await agents["trace"].record_state(decision_result)
    assert trace_result is None
    
    # Verify final state
    assert decision_result.section_number > 0
    assert decision_result.character is not None
    if decision_result.rules and decision_result.rules.needs_dice:
        assert decision_result.rules.dice_type is not None

@pytest.mark.asyncio
async def test_error_propagation(agents, sample_character):
    """Test error handling and propagation between agents."""
    # Create error state
    error_state = GameState(
        section_number=999,  # Invalid section
        player_input="test",
        character=sample_character,
        last_update=datetime.now()
    )
    
    # Try to process through agent chain
    narrator_result = await agents["narrator"].process_section(error_state.section_number)
    assert narrator_result.error is not None
    
    rules_result = await agents["rules"].process_section_rules(error_state.section_number)
    assert rules_result.error is not None
    
    decision_result = await agents["decision"].analyze_decision(error_state)
    assert decision_result.error is not None
    
    # Verify error is traced
    trace_result = await agents["trace"].record_state(decision_result)
    assert trace_result is None
    
    current_trace = await agents["trace"]._manager.get_current_trace()
    assert current_trace.history[-1].action_type == "ERROR"
