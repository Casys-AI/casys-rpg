"""Tests for decision model."""
import pytest
from datetime import datetime
from models.decision_model import DecisionModel, DiceResult, AnalysisResult
from models.rules_model import DiceType
from models.trace_model import ActionType

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

def test_decision_model_creation():
    """Test creation and validation of decision models."""
    # Test basic creation
    decision = DecisionModel(section_number=1)
    assert decision.section_number == 1
    assert decision.awaiting_action == ActionType.USER_INPUT
    assert isinstance(decision.timestamp, datetime)
    
    # Test with conditions
    decision = DecisionModel(
        section_number=1,
        conditions=["has_key", "has_key", "is_strong"]  # Duplicate condition
    )
    assert len(decision.conditions) == 2  # Duplicates should be removed
    assert "has_key" in decision.conditions
    assert "is_strong" in decision.conditions

def test_decision_model_validation():
    """Test validation rules of decision model."""
    # Test invalid section number
    with pytest.raises(ValueError):
        DecisionModel(section_number=0)
    
    with pytest.raises(ValueError):
        DecisionModel(section_number=-1)

def test_decision_model_custom_action():
    """Test decision model with different action types."""
    decision = DecisionModel(
        section_number=1,
        awaiting_action=ActionType.DICE_ROLL
    )
    assert decision.awaiting_action == ActionType.DICE_ROLL

def test_decision_model_conditions_management():
    """Test conditions list management in decision model."""
    # Test adding duplicate conditions
    conditions = ["condition1", "condition2", "condition1", "condition3"]
    decision = DecisionModel(section_number=1, conditions=conditions)
    
    # Check that duplicates are removed
    assert len(decision.conditions) == 3
    assert decision.conditions == ["condition1", "condition2", "condition3"]
