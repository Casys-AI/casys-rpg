"""Tests for rules model."""
import pytest
from datetime import datetime
from models.rules_model import RulesModel, DiceType, SourceType, Choice, ChoiceType

def test_rules_model_creation():
    """Test basic creation of rules model."""
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
    # Test avec needs_user_response
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
        next_action="dice_first"
    )
    assert rules_dice.next_action == "dice_first"
    
    # Test avec une valeur invalide
    with pytest.raises(ValueError):
        RulesModel(
            section_number=1,
            needs_user_response=True,
            next_action="invalid_action"
        )
    
    # Test sans needs_dice ni needs_user_response
    with pytest.raises(ValueError):
        RulesModel(
            section_number=1,
            next_action="user_first"  # Devrait échouer car aucune action n'est nécessaire
        )

def test_rules_model_source_types():
    """Test different source types."""
    for source_type in SourceType:
        rules = RulesModel(
            section_number=1,
            source_type=source_type
        )
        assert rules.source_type == source_type

def test_rules_model_with_error():
    """Test rules model in error state."""
    error_message = "Test error message"
    rules = RulesModel(
        section_number=1,
        error=error_message,
        source_type=SourceType.ERROR
    )
    
    assert rules.error == error_message
    assert rules.source_type == SourceType.ERROR
