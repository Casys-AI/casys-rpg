"""Tests for decision model."""
import pytest
from datetime import datetime
from models.decision_model import DecisionModel, DiceResult, AnalysisResult
from models.rules_model import DiceType
from models.trace_model import ActionType

@pytest.fixture
def sample_decision_model():
    return DecisionModel(
        section_number=1,
        choices={"1": "Choice 1", "2": "Choice 2"}
    )

def test_decision_model_creation(sample_decision_model):
    """Test creation and validation of decision models."""
    assert sample_decision_model.section_number == 1
    assert "Choice 1" in sample_decision_model.choices.values()
    assert "Choice 2" in sample_decision_model.choices.values()
    assert sample_decision_model.selected_choice is None
    assert isinstance(sample_decision_model.timestamp, datetime)

def test_decision_model_empty_creation():
    """Test basic creation of decision model."""
    decision = DecisionModel(section_number=1)
    assert decision.section_number == 1
    assert decision.choices == {}
    assert decision.selected_choice is None
    assert isinstance(decision.timestamp, datetime)

def test_dice_result_creation():
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
    assert len(analysis.conditions) == 2
    assert analysis.analysis == "Player chose to fight"
    
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
    
    # Test invalid choice key
    with pytest.raises(ValueError):
        DecisionModel(
            section_number=1,
            choices={"": "Empty key not allowed"}
        )
    
    # Test invalid choice value
    with pytest.raises(ValueError):
        DecisionModel(
            section_number=1,
            choices={"1": ""}
        )

def test_decision_model_choice_selection(sample_decision_model):
    """Test choice selection in decision model."""
    # Test valid choice selection
    updated_model = sample_decision_model.model_copy(update={"selected_choice": "1"})
    assert updated_model.selected_choice == "1"
    
    # Test invalid choice selection
    with pytest.raises(ValueError):
        sample_decision_model.model_copy(update={"selected_choice": "invalid_choice"})

def test_decision_model_choice_validation():
    """Test choice validation in decision model."""
    # Test duplicate choice keys
    choices = {
        "1": "Choice 1",
        "2": "Choice 2",
        "1": "Duplicate key"  # This should be ignored by Python dict
    }
    decision = DecisionModel(section_number=1, choices=choices)
    assert len(decision.choices) == 2
    assert decision.choices["1"] == "Choice 1"

def test_decision_model_immutability(sample_decision_model):
    """Test immutability of decision model."""
    # Attempt to modify choices
    with pytest.raises(TypeError):
        sample_decision_model.choices["3"] = "New choice"
    
    # Verify original choices are unchanged
    assert len(sample_decision_model.choices) == 2
    assert "3" not in sample_decision_model.choices

def test_decision_model_serialization(sample_decision_model):
    """Test serialization of decision model."""
    model_dict = sample_decision_model.model_dump()
    
    assert model_dict["section_number"] == 1
    assert model_dict["choices"] == {"1": "Choice 1", "2": "Choice 2"}
    assert model_dict["selected_choice"] is None
    assert isinstance(model_dict["timestamp"], datetime)
