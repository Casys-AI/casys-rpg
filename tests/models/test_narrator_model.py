"""Tests for narrator model."""
import pytest
from datetime import datetime
from models.narrator_model import NarratorModel, SourceType

def test_narrator_model_creation(sample_narrator_model):
    """Test basic creation of narrator model."""
    assert sample_narrator_model.section_number == 1
    assert sample_narrator_model.content == "Sample formatted content"
    assert sample_narrator_model.source_type == SourceType.PROCESSED
    assert sample_narrator_model.error is None
    assert isinstance(sample_narrator_model.timestamp, datetime)

def test_narrator_model_empty_creation():
    """Test creation of empty narrator model."""
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
    assert SourceType.RAW == "raw"
    assert SourceType.PROCESSED == "processed"
    assert SourceType.ERROR == "error"
    
    narrator_raw = NarratorModel(section_number=1, source_type=SourceType.RAW)
    assert narrator_raw.source_type == SourceType.RAW
    
    narrator_processed = NarratorModel(section_number=1, source_type=SourceType.PROCESSED)
    assert narrator_processed.source_type == SourceType.PROCESSED
    
    narrator_error = NarratorModel(section_number=1, source_type=SourceType.ERROR)
    assert narrator_error.source_type == SourceType.ERROR

def test_narrator_model_content_update(sample_narrator_model):
    """Test updating narrator model content."""
    new_content = "Updated content"
    updated_model = sample_narrator_model.model_copy(update={"content": new_content})
    
    assert updated_model.content == new_content
    assert updated_model.section_number == sample_narrator_model.section_number
    assert updated_model.source_type == sample_narrator_model.source_type

def test_narrator_model_error_handling():
    """Test error handling in narrator model."""
    # Test that error and content cannot coexist
    with pytest.raises(ValueError):
        NarratorModel(
            section_number=1,
            content="Some content",
            error="Some error"
        )
    
    # Test that error forces source_type to ERROR
    narrator = NarratorModel(
        section_number=1,
        error="Test error",
        source_type=SourceType.RAW  # This should be overridden
    )
    assert narrator.source_type == SourceType.ERROR
