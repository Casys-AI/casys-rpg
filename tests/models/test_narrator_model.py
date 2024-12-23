"""Tests for narrator model."""
import pytest
from datetime import datetime
from models.narrator_model import NarratorModel, SourceType

def test_narrator_model_creation():
    """Test basic creation of narrator model."""
    narrator = NarratorModel(section_number=1)
    
    assert narrator.section_number == 1
    assert narrator.content == ""
    assert narrator.source_type == SourceType.RAW
    assert narrator.error is None
    assert isinstance(narrator.timestamp, datetime)

def test_narrator_model_with_content():
    """Test narrator model with content."""
    content = "This is a test narrative section."
    narrator = NarratorModel(
        section_number=1,
        content=content,
        source_type=SourceType.PROCESSED
    )
    
    assert narrator.content == content
    assert narrator.source_type == SourceType.PROCESSED

def test_narrator_model_with_error():
    """Test narrator model in error state."""
    error_msg = "Failed to load section"
    narrator = NarratorModel(
        section_number=1,
        error=error_msg,
        source_type=SourceType.ERROR
    )
    
    assert narrator.error == error_msg
    assert narrator.source_type == SourceType.ERROR

def test_narrator_model_invalid_section():
    """Test narrator model with invalid section number."""
    with pytest.raises(ValueError):
        NarratorModel(section_number=0)
    
    with pytest.raises(ValueError):
        NarratorModel(section_number=-1)

def test_narrator_model_custom_timestamp():
    """Test narrator model with custom timestamp."""
    custom_time = datetime(2024, 1, 1, 12, 0)
    narrator = NarratorModel(
        section_number=1,
        timestamp=custom_time
    )
    
    assert narrator.timestamp == custom_time

def test_narrator_model_source_type_enum():
    """Test source type enumeration values."""
    # Test all valid source types
    for source_type in SourceType:
        narrator = NarratorModel(
            section_number=1,
            source_type=source_type
        )
        assert narrator.source_type == source_type
    
    # Test invalid source type
    with pytest.raises(ValueError):
        NarratorModel(
            section_number=1,
            source_type="invalid_type"  # type: ignore
        )

def test_narrator_model_content_update():
    """Test updating narrator model content."""
    narrator = NarratorModel(section_number=1)
    
    # Update content and source type
    new_content = "Updated content"
    narrator.content = new_content
    narrator.source_type = SourceType.PROCESSED
    
    assert narrator.content == new_content
    assert narrator.source_type == SourceType.PROCESSED

def test_narrator_model_error_handling():
    """Test error handling in narrator model."""
    narrator = NarratorModel(section_number=1)
    
    # Set error state
    error_msg = "Test error"
    narrator.error = error_msg
    narrator.source_type = SourceType.ERROR
    
    assert narrator.error == error_msg
    assert narrator.source_type == SourceType.ERROR
    
    # Clear error state
    narrator.error = None
    narrator.source_type = SourceType.RAW
    
    assert narrator.error is None
    assert narrator.source_type == SourceType.RAW
