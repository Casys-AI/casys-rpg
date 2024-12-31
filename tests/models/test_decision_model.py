"""Tests for decision model."""
import pytest
from datetime import datetime
from models.decision_model import (
    DecisionModel,
    DiceResult,
    AnalysisResult,
    DiceType
)
from models.trace_model import ActionType
from models.types.common_types import NextActionType

@pytest.fixture
def sample_decision_model():
    """Create a sample decision model for testing."""
    return DecisionModel(
        section_number=1,
        next_section=2,
        awaiting_action=ActionType.USER_INPUT,
        next_action=NextActionType.USER_FIRST,
        conditions=["initial_condition"]
    )

def test_decision_model_creation(sample_decision_model):
    """Test creation and validation of decision models."""
    assert sample_decision_model.section_number == 1
    assert sample_decision_model.next_section == 2
    assert sample_decision_model.awaiting_action == ActionType.USER_INPUT
    assert sample_decision_model.next_action == NextActionType.USER_FIRST
    assert sample_decision_model.conditions == ["initial_condition"]
    assert sample_decision_model.error is None
    assert isinstance(sample_decision_model.timestamp, datetime)

def test_decision_model_empty_creation():
    """Test basic creation of decision model."""
    decision = DecisionModel(section_number=1)
    assert decision.section_number == 1
    assert decision.next_section is None
    assert decision.conditions == []
    assert decision.error is None
    assert isinstance(decision.timestamp, datetime)

def test_dice_result_validation():
    """Test creation and validation of dice results."""
    # Test valid dice result
    dice = DiceResult(value=6, type=DiceType.COMBAT)
    assert dice.value == 6
    assert dice.type == DiceType.COMBAT
    assert isinstance(dice.timestamp, datetime)
    
    # Test invalid dice value
    with pytest.raises(ValueError):
        DiceResult(value=7, type=DiceType.CHANCE)
    
    with pytest.raises(ValueError):
        DiceResult(value=0, type=DiceType.CHANCE)
    
    # Test optional value
    dice = DiceResult(type=DiceType.COMBAT)
    assert dice.value is None

def test_analysis_result_validation():
    """Test creation and validation of analysis results."""
    # Test valid analysis
    analysis = AnalysisResult(
        next_section=1,
        conditions=["has_sword", "is_brave"],
        analysis="Player chose to fight"
    )
    assert analysis.next_section == 1
    assert analysis.conditions == ["has_sword", "is_brave"]
    assert analysis.analysis == "Player chose to fight"
    assert analysis.error is None
    
    # Test invalid next section
    with pytest.raises(ValueError):
        AnalysisResult(next_section=0)
    
    # Test empty conditions
    analysis = AnalysisResult(next_section=1)
    assert analysis.conditions == []

def test_decision_model_validation():
    """Test validation rules of decision model."""
    # Test invalid section number
    with pytest.raises(ValueError):
        DecisionModel(section_number=0)
    
    with pytest.raises(ValueError):
        DecisionModel(section_number=-1)
    
    # Test invalid next_section
    with pytest.raises(ValueError):
        DecisionModel(
            section_number=1,
            next_section=0
        )
    
    with pytest.raises(ValueError):
        DecisionModel(
            section_number=1,
            next_section=-1
        )
    
    # Test valid model with optional fields
    model = DecisionModel(
        section_number=1,
        next_section=2,
        conditions=["test_condition"]
    )
    assert model.section_number == 1
    assert model.next_section == 2
    assert model.conditions == ["test_condition"]
    assert model.error is None

def test_decision_model_update(sample_decision_model):
    """Test updating decision model fields."""
    # Test direct update
    sample_decision_model.next_section = 3
    assert sample_decision_model.next_section == 3
    
    # Test conditions update
    sample_decision_model.conditions.append("new_condition")
    assert "new_condition" in sample_decision_model.conditions
    
    # Test model_copy update
    updated = sample_decision_model.model_copy(
        update={"conditions": ["different_condition"]}
    )
    assert "different_condition" in updated.conditions
    assert "new_condition" in sample_decision_model.conditions
    assert isinstance(updated.conditions, list)
    assert isinstance(sample_decision_model.conditions, list)

def test_decision_model_serialization(sample_decision_model):
    """Test serialization of decision model."""
    json_data = sample_decision_model.model_dump_json()
    loaded = DecisionModel.model_validate_json(json_data)
    
    assert loaded.section_number == sample_decision_model.section_number
    assert loaded.next_section == sample_decision_model.next_section
    assert loaded.awaiting_action == sample_decision_model.awaiting_action
    assert loaded.next_action == sample_decision_model.next_action
