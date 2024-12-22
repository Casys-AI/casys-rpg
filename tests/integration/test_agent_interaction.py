"""Integration tests for agent interactions."""
import pytest
import pytest_asyncio
from datetime import datetime

from agents.factories.game_factory import GameFactory
from config.game_config import GameConfig
from models.game_state import GameState
from models.character_model import CharacterModel
from models.rules_model import RulesModel, DiceType
from models.narrator_model import NarratorModel
from models.trace_model import TraceModel

@pytest.fixture
def game_config():
    """Create a test game configuration."""
    return GameConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def agents(game_config):
    """Create test agents."""
    factory = GameFactory(config=game_config)
    return {
        "narrator": factory.create_narrator_agent(),
        "rules": factory.create_rules_agent(),
        "decision": factory.create_decision_agent(),
        "trace": factory.create_trace_agent()
    }

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
async def test_rules_decision_interaction(agents):
    """Test interaction between rules and decision agents."""
    # Create game state
    state = GameState(
        section_number=1,
        player_input="test choice",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # Get rules
    rules_result = await agents["rules"].process_section_rules(1)
    assert isinstance(rules_result, RulesModel)
    
    # Make decision based on rules
    state.available_choices = rules_result.next_sections
    decision_result = await agents["decision"].analyze_decision(state)
    
    # Verify decision considers rules
    assert isinstance(decision_result, GameState)
    assert decision_result.needs_dice_roll == rules_result.needs_dice_roll
    assert decision_result.dice_type == rules_result.dice_type

@pytest.mark.asyncio
async def test_decision_trace_interaction(agents):
    """Test interaction between decision and trace agents."""
    # Create game state
    state = GameState(
        section_number=1,
        player_input="test choice",
        character=sample_character(),
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
async def test_full_agent_chain(agents):
    """Test complete chain of agent interactions."""
    # Initial state
    state = GameState(
        section_number=1,
        player_input="start game",
        character=sample_character(),
        last_update=datetime.now()
    )
    
    # 1. Get section content
    narrator_result = await agents["narrator"].process_section(state.section_number)
    assert isinstance(narrator_result, NarratorModel)
    
    # 2. Get rules
    rules_result = await agents["rules"].process_section_rules(state.section_number)
    assert isinstance(rules_result, RulesModel)
    
    # 3. Update state with rules
    state.available_choices = rules_result.next_sections
    state.needs_dice_roll = rules_result.needs_dice_roll
    state.dice_type = rules_result.dice_type
    
    # 4. Make decision
    decision_result = await agents["decision"].analyze_decision(state)
    assert isinstance(decision_result, GameState)
    
    # 5. Record trace
    trace_result = await agents["trace"].record_state(decision_result)
    assert trace_result is None
    
    # Verify final state
    assert decision_result.section_number > 0
    assert decision_result.character is not None
    if decision_result.needs_dice_roll:
        assert decision_result.dice_type is not None

@pytest.mark.asyncio
async def test_error_propagation(agents):
    """Test error handling and propagation between agents."""
    # Create error state
    error_state = GameState(
        section_number=999,  # Invalid section
        player_input="test",
        character=sample_character(),
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
