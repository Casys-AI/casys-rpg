"""Tests for the MarkdownFormatter utility."""

import pytest
from datetime import datetime

from utils.markdown_formatter import MarkdownFormatter
from models.narrator_model import SourceType

@pytest.fixture
def sample_content():
    return """# Section 1
    
This is a test section with some content.

## Subsection
- Point 1
- Point 2
"""

@pytest.fixture
def sample_metadata():
    return {
        "section": 1,
        "timestamp": "2024-12-23T22:19:40",
        "source_type": SourceType.PROCESSED.value
    }

def test_content_to_markdown_without_metadata():
    """Test converting content to markdown without metadata."""
    content = "# Test\nSome content"
    result = MarkdownFormatter.content_to_markdown(content)
    assert result == content

def test_content_to_markdown_with_metadata(sample_content, sample_metadata):
    """Test converting content to markdown with metadata."""
    result = MarkdownFormatter.content_to_markdown(sample_content, sample_metadata)
    assert "---" in result
    assert "section: 1" in result
    assert "timestamp:" in result
    assert "source_type:" in result
    assert sample_content in result

def test_markdown_to_content_valid():
    """Test parsing valid markdown content."""
    content = """# Section 1
Some content"""
    result = MarkdownFormatter.markdown_to_content(content, 1)
    assert result == content

def test_markdown_to_content_invalid_section():
    """Test parsing markdown with wrong section number."""
    content = """# Section 2
Some content"""
    result = MarkdownFormatter.markdown_to_content(content, 1)
    assert result is None

def test_markdown_to_content_with_frontmatter(sample_metadata):
    """Test parsing markdown with frontmatter."""
    content = """---
section: 1
timestamp: 2024-12-23T22:19:40
source_type: processed
---

# Section 1
Some content"""
    result = MarkdownFormatter.markdown_to_content(content, 1)
    assert "# Section 1" in result
    assert "Some content" in result
    assert "---" not in result

def test_validate_markdown_valid(sample_content):
    """Test validating valid markdown."""
    assert MarkdownFormatter.validate_markdown(sample_content) is True

def test_validate_markdown_no_header():
    """Test validating markdown without headers."""
    content = "Just some text\nwithout headers"
    assert MarkdownFormatter.validate_markdown(content) is False

def test_validate_markdown_empty():
    """Test validating empty markdown."""
    assert MarkdownFormatter.validate_markdown("") is False
