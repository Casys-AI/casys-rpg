"""Tests for the rules manager module."""
import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from managers.rules_manager import RulesManager
from config.storage_config import StorageConfig
from models.rules_model import RulesModel, DiceType, SourceType, Choice, ChoiceType
from models.errors_model import RulesError

@pytest.fixture
def mock_cache_manager():
    """Create a mock cache manager."""
    cache = Mock()
    cache.save_cached_content = AsyncMock()
    cache.get_cached_content = AsyncMock()
    cache.load_raw_content = AsyncMock()
    cache.exists_raw_content = AsyncMock()
    return cache

@pytest.fixture
def config():
    """Create a test storage config."""
    return StorageConfig.get_default_config(base_path="./test_data")

@pytest_asyncio.fixture
async def rules_manager(config, mock_cache_manager):
    """Create a test rules manager."""
    manager = RulesManager(config=config, cache_manager=mock_cache_manager)
    return manager

@pytest.fixture
def sample_choices():
    """Create sample choices."""
    return [
        Choice(
            text="Choice 1",
            type=ChoiceType.DIRECT,
            target_section=2
        ),
        Choice(
            text="Choice 2",
            type=ChoiceType.CONDITIONAL,
            target_section=3,
            conditions=["has_sword", "health > 10"]
        )
    ]

@pytest.fixture
def sample_rules_model(sample_choices):
    """Create a sample rules model."""
    return RulesModel(
        section_number=1,
        last_update=datetime.now(),
        source="test_source",
        source_type=SourceType.RAW,
        needs_dice=True,
        dice_type=DiceType.COMBAT,
        needs_user_response=True,
        next_action="user_first",
        conditions=["condition1", "condition2"],
        choices=sample_choices,
        rules_summary="Test rules summary",
        error=None
    )

@pytest.fixture
def sample_rules_markdown():
    """Create sample rules markdown."""
    return """
# Rules for Section 1

## Metadata
- Last_Update: 2024-12-22T12:00:00
- Source: test_source
- Source_Type: raw

## Analysis
- Needs_Dice: true
- Dice_Type: combat
- Needs_User_Response: true
- Next_Action: user_first
- Conditions: condition1, condition2
- Next_Sections: 2, 3

## Choices
* Choice 1 (Type: direct)
  - Target: Section 2

* Choice 2 (Type: conditional)
  - Target: Section 3
  - Conditions: has_sword, health > 10

## Summary
Test rules summary

## Error
None
"""

@pytest.mark.asyncio
async def test_get_rules_content(rules_manager, mock_cache_manager, sample_rules_markdown):
    """Test getting rules content."""
    # Configure mock
    mock_cache_manager.load_raw_content.return_value = sample_rules_markdown
    mock_cache_manager.get_cached_content.return_value = sample_rules_markdown
    
    # Test successful retrieval
    content = await rules_manager.get_rules_content(1)
    assert content == sample_rules_markdown
    mock_cache_manager.get_cached_content.assert_called_once_with(
        key=f"section_1_rules",
        namespace="rules"
    )
    
    # Test non-existent rules
    mock_cache_manager.get_cached_content.return_value = None
    content = await rules_manager.get_rules_content(999)
    assert content is None

@pytest.mark.asyncio
async def test_get_existing_rules_cache_hit(rules_manager, mock_cache_manager, sample_rules_model, sample_rules_markdown):
    """Test getting existing rules with cache hit."""
    # Configure mock for cache hit
    mock_cache_manager.get_cached_content.return_value = sample_rules_markdown
    
    result = await rules_manager.get_existing_rules(1)
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.needs_dice is True
    assert result.dice_type == DiceType.COMBAT
    
    # Verify cache was checked once
    mock_cache_manager.get_cached_content.assert_called_once()
    mock_cache_manager.exists_raw_content.assert_not_called()
    mock_cache_manager.load_raw_content.assert_not_called()

@pytest.mark.asyncio
async def test_get_existing_rules_cache_miss(rules_manager, mock_cache_manager, sample_rules_model, sample_rules_markdown):
    """Test getting existing rules with cache miss but raw content exists."""
    # Configure mock for cache miss but raw content exists
    mock_cache_manager.get_cached_content.return_value = None
    mock_cache_manager.exists_raw_content.return_value = True
    mock_cache_manager.load_raw_content.return_value = sample_rules_markdown
    
    result = await rules_manager.get_existing_rules(1)
    assert isinstance(result, RulesModel)
    assert result.section_number == 1
    assert result.source_type == SourceType.RAW
    assert len(result.choices) == 2
    assert result.choices[0].type == ChoiceType.DIRECT
    assert result.choices[1].type == ChoiceType.CONDITIONAL
    
    # Verify cache was checked once, then raw content was loaded
    mock_cache_manager.get_cached_content.assert_called_once()
    mock_cache_manager.exists_raw_content.assert_called_once()
    mock_cache_manager.load_raw_content.assert_called_once()

@pytest.mark.asyncio
async def test_save_rules(rules_manager, mock_cache_manager, sample_rules_model):
    """Test saving rules."""
    # Test successful save
    await rules_manager.save_rules(sample_rules_model)
    mock_cache_manager.save_cached_content.assert_called_once()
    
    # Verify the saved content
    call_args = mock_cache_manager.save_cached_content.call_args
    assert call_args[1]["namespace"] == "rules"
    assert call_args[1]["key"] == f"section_{sample_rules_model.section_number}_rules"

def test_markdown_conversion(rules_manager, sample_rules_model, sample_rules_markdown):
    """Test markdown conversion methods."""
    # Test rules to markdown
    markdown = rules_manager._rules_to_markdown(sample_rules_model)
    assert isinstance(markdown, str)
    assert "# Rules for Section 1" in markdown
    assert "## Metadata" in markdown
    assert "## Analysis" in markdown
    assert "## Choices" in markdown

    # Test markdown to rules
    rules = rules_manager._markdown_to_rules(sample_rules_markdown, 1)
    assert isinstance(rules, RulesModel)
    assert rules.section_number == 1
    assert rules.needs_dice is True
    assert rules.dice_type == DiceType.COMBAT
    assert len(rules.conditions) == 2
    assert len(rules.choices) == 2
    assert rules.choices[0].type == ChoiceType.DIRECT
    assert rules.choices[1].type == ChoiceType.CONDITIONAL
    # Vérifier que les sections cibles sont bien définies
    assert rules.choices[0].target_section is not None
    assert rules.choices[1].target_section is not None

def test_markdown_conversion_invalid_content(rules_manager):
    """Test markdown conversion with invalid or incomplete content."""
    # Test with missing sections
    invalid_markdown = """# Section 1"""
    rules = rules_manager._markdown_to_rules(invalid_markdown, 1)
    assert rules is None

    # Test with missing required fields
    incomplete_markdown = """# Rules for Section 1

## Metadata
- Last_Update: 2024-12-22T12:00:00
- Source: test_source
- Source_Type: raw

## Analysis
- Target_Sections: 2, 3

## Choices
* Choice 1 (Type: direct)
  - Target: Section 2

## Summary
Test summary

## Error
None
"""
    rules = rules_manager._markdown_to_rules(incomplete_markdown, 1)
    assert rules is None

    # Test with empty Analysis section
    no_analysis_markdown = """# Rules for Section 1

## Metadata
- Last_Update: 2024-12-22T12:00:00
- Source: test_source
- Source_Type: raw

## Analysis

## Choices
* Choice 1 (Type: direct)
  - Target: Section 2

## Summary
Test summary

## Error
None
"""
    rules = rules_manager._markdown_to_rules(no_analysis_markdown, 1)
    assert rules is None
