"""Tests for rules model."""
import pytest
from datetime import datetime
from models.rules_model import (
    RulesModel, DiceType, Choice, ChoiceType,
    SourceType
)
from models.types.common_types import NextActionType

@pytest.fixture
def sample_rules_model():
    """Create a sample rules model for testing."""
    return RulesModel(
        section_number=1,
        dice_type=DiceType.COMBAT,
        needs_dice=True,
        needs_user_response=True,
        next_action=NextActionType.USER_FIRST,
        conditions=["has_sword"],
        choices=[
            Choice(
                text="Go to section 2",
                type=ChoiceType.DIRECT,
                target_section=2
            ),
            Choice(
                text="Use sword if you have it",
                type=ChoiceType.CONDITIONAL,
                conditions=["has_sword"],
                target_section=3
            )
        ]
    )

def test_rules_model_creation(sample_rules_model):
    """Test basic creation of rules model."""
    assert sample_rules_model.section_number == 1
    assert sample_rules_model.dice_type == DiceType.COMBAT
    assert sample_rules_model.needs_dice
    assert sample_rules_model.needs_user_response
    assert sample_rules_model.next_action == NextActionType.USER_FIRST
    assert isinstance(sample_rules_model.last_update, datetime)

def test_rules_model_empty_creation():
    """Test creation of empty rules model."""
    rules = RulesModel(section_number=1)
    
    assert rules.section_number == 1
    assert rules.dice_type == DiceType.NONE
    assert not rules.needs_dice
    assert not rules.needs_user_response
    assert rules.next_action is None
    assert isinstance(rules.last_update, datetime)

def test_rules_model_with_dice():
    """Test rules model with dice configuration."""
    rules = RulesModel(
        section_number=1,
        dice_type=DiceType.CHANCE,
        needs_dice=True
    )
    
    assert rules.dice_type == DiceType.CHANCE
    assert rules.needs_dice
    assert not rules.needs_user_response

def test_rules_model_with_choices():
    """Test rules model with choices and next sections."""
    choice = Choice(
        text="Go to castle",
        type=ChoiceType.DIRECT,
        target_section=2
    )
    
    rules = RulesModel(
        section_number=1,
        choices=[choice]
    )
    
    assert len(rules.choices) == 1
    assert rules.choices[0].text == "Go to castle"
    assert rules.choices[0].target_section == 2
    assert rules.needs_user_response  # Should be True when there are choices

def test_rules_model_with_conditional_choices():
    """Test rules model with conditional choices."""
    choice = Choice(
        text="Fight monster",
        type=ChoiceType.CONDITIONAL,
        conditions=["has_sword", "health > 50"]
    )
    
    rules = RulesModel(
        section_number=1,
        choices=[choice]
    )
    
    assert len(rules.choices) == 1
    assert rules.choices[0].type == ChoiceType.CONDITIONAL
    assert len(rules.choices[0].conditions) == 2
    assert rules.needs_user_response

def test_rules_model_with_dice_choices():
    """Test rules model with dice-based choices."""
    choice = Choice(
        text="Test your luck",
        type=ChoiceType.DICE,
        dice_type=DiceType.CHANCE,
        dice_results={"success": 2, "failure": 3}
    )
    
    rules = RulesModel(
        section_number=1,
        choices=[choice]
    )
    
    assert len(rules.choices) == 1
    assert rules.choices[0].type == ChoiceType.DICE
    assert rules.choices[0].dice_type == DiceType.CHANCE
    assert rules.needs_dice

def test_rules_model_validation_section_number():
    """Test section number validation."""
    with pytest.raises(ValueError):
        RulesModel(section_number=0)  # Section numbers must be positive
        
    with pytest.raises(ValueError):
        RulesModel(section_number=-1)

def test_rules_model_next_action_validation():
    """Test next_action field validation."""
    # Test with user_first
    rules_user = RulesModel(
        section_number=1,
        needs_user_response=True,
        next_action="user_first"
    )
    assert rules_user.next_action == "user_first"
    
    # Test avec needs_dice
    rules_dice = RulesModel(
        section_number=1,
        needs_dice=True,
        dice_type=DiceType.COMBAT,
        next_action="dice_first"
    )
    assert rules_dice.next_action == "dice_first"
    
    # Test invalid next_action
    with pytest.raises(ValueError):
        RulesModel(
            section_number=1,
            needs_user_response=True,
            next_action="invalid"
        )
    
    # Test next_action sans needs_dice ou needs_user_response
    with pytest.raises(ValueError):
        RulesModel(
            section_number=1,
            next_action="user_first"
        )

def test_rules_model_source_types():
    """Test source type enumeration values."""
    assert SourceType.RAW == "raw"
    assert SourceType.PROCESSED == "processed"
    assert SourceType.ERROR == "error"
    
    rules_raw = RulesModel(section_number=1, source_type=SourceType.RAW)
    assert rules_raw.source_type == SourceType.RAW
    
    rules_processed = RulesModel(section_number=1, source_type=SourceType.PROCESSED)
    assert rules_processed.source_type == SourceType.PROCESSED
    
    rules_error = RulesModel(section_number=1, source_type=SourceType.ERROR)
    assert rules_error.source_type == SourceType.ERROR

def test_rules_model_with_error():
    """Test rules model in error state."""
    error_msg = "Failed to process rules"
    rules = RulesModel(
        section_number=1,
        error=error_msg,
        source_type=SourceType.ERROR
    )
    
    assert rules.error == error_msg
    assert rules.source_type == SourceType.ERROR
    assert not rules.needs_dice
    assert not rules.needs_user_response

def test_rules_model_choice_validation():
    """Test choice validation in rules model."""
    # Test invalid choice type
    with pytest.raises(ValueError):
        Choice(
            text="Invalid choice",
            type="invalid_type",  # type: ignore
            target_section=2
        )
    
    # Test missing target section for direct choice
    with pytest.raises(ValueError):
        Choice(
            text="Invalid direct choice",
            type=ChoiceType.DIRECT
        )
    
    # Test missing conditions for conditional choice
    with pytest.raises(ValueError):
        Choice(
            text="Invalid conditional choice",
            type=ChoiceType.CONDITIONAL
        )
    
    # Test missing dice_type for dice choice
    with pytest.raises(ValueError):
        Choice(
            text="Invalid dice choice",
            type=ChoiceType.DICE
        )

def test_choice_validation():
    """Test validation rules for choices."""
    # Test invalid choice key
    with pytest.raises(ValueError):
        Choice(
            text="",
            type=ChoiceType.DIRECT,
            target_section=1
        )
    
    # Test direct choice validation
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.DIRECT,
            conditions=["has_sword"]  # Direct choices can't have conditions
        )
    
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.DIRECT,
            dice_type=DiceType.COMBAT  # Direct choices can't have dice
        )
    
    # Test conditional choice validation
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.CONDITIONAL,
            target_section=1,
            dice_type=DiceType.COMBAT  # Conditional choices can't have dice
        )
    
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.CONDITIONAL,
            target_section=1  # Must have conditions
        )
    
    # Test dice choice validation
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.DICE,
            conditions=["has_sword"]  # Dice choices can't have conditions
        )
    
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.DICE,
            target_section=1  # Must have dice_results
        )
    
    # Test mixed choice validation
    with pytest.raises(ValueError):
        Choice(
            text="Test choice",
            type=ChoiceType.MIXED,
            target_section=1  # Must have both conditions and dice
        )
    
    # Test valid choices
    direct = Choice(
        text="Go to section 2",
        type=ChoiceType.DIRECT,
        target_section=2
    )
    assert direct.target_section == 2
    
    conditional = Choice(
        text="Use sword if you have it",
        type=ChoiceType.CONDITIONAL,
        conditions=["has_sword"],
        target_section=3
    )
    assert "has_sword" in conditional.conditions
    
    dice = Choice(
        text="Roll for combat",
        type=ChoiceType.DICE,
        dice_type=DiceType.COMBAT,
        dice_results={"1-3": 4, "4-6": 5}
    )
    assert dice.dice_type == DiceType.COMBAT
    
    mixed = Choice(
        text="Use sword in combat",
        type=ChoiceType.MIXED,
        conditions=["has_sword"],
        dice_type=DiceType.COMBAT,
        dice_results={"1-3": 6, "4-6": 7}
    )
    assert mixed.type == ChoiceType.MIXED
