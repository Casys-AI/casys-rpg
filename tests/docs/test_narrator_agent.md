# Test Documentation: Narrator Agent

## Overview
This document details the test suite for the Narrator Agent component, which manages content loading, formatting, and presentation in the game system.

## Test Infrastructure

### Fixtures

#### `content_dir`
**Purpose**: Provides test content environment
**Setup**:
```python
temp_dir = tempfile.mkdtemp()
cache_dir = os.path.join(temp_dir, "cache")
os.makedirs(cache_dir)

# Test content creation with representative game book content
test_content = """La Forêt Mystérieuse

Vous arrivez à l'orée d'une forêt sombre. Les arbres semblent murmurer des secrets anciens.

Que souhaitez-vous faire ?

1. Explorer plus profondément dans la forêt
2. Retourner au village
3. Examiner les traces au sol"""

with open(os.path.join(temp_dir, "1.md"), "w", encoding="utf-8") as f:
    f.write(test_content)
```

#### `narrator_agent`
**Configuration**:
```python
config = NarratorConfig(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    content_directory=content_dir,
    cache_directory=cache_dir
)
```

## Detailed Test Cases

### 1. Cache Usage (`test_narrator_agent_cache`)
**Purpose**: Verify that cached content is used directly when available

#### Test Sequence:
```python
# Create cached content
cached_content = "This is a cached content that should be used directly"
with open(cache_path, "w") as f:
    f.write(cached_content)

# Verify cache usage
async for result in narrator_agent.ainvoke({"state": {"section_number": section}}):
    assert result["state"]["content"] == cached_content
    assert result["state"]["source"] == "cache"
```

### 2. No Cache Processing (`test_narrator_agent_no_cache`)
**Purpose**: Verify content processing when no cache exists

#### Test Sequence:
```python
# Create source content without cache
test_content = """Test Section

This is a test section with some *italic* text."""

# Verify processing
async for result in narrator_agent.ainvoke({"state": {"section_number": section}}):
    assert content != test_content  # Content should be formatted
    assert "**" in content  # Should contain Markdown formatting
    assert result["state"]["source"] in ["loaded", "cache"]
```

### 3. Invalid Input (`test_narrator_agent_invalid_input`)
**Purpose**: Test error handling for invalid inputs

#### Validations:
```python
async for result in narrator_agent.ainvoke({"state": {}}):
    assert "error" in result["state"]
```

### 4. Missing Section (`test_narrator_agent_section_not_found`)
**Purpose**: Test handling of non-existent sections

#### Validations:
```python
async for result in narrator_agent.ainvoke({"state": {"section_number": 999}}):
    assert "error" in result["state"]
    assert result["state"]["error"] == "Section 999 not found"
    assert result["state"]["source"] == "not_found"
```

### 5. Content Format (`test_narrator_agent_content_format`)
**Purpose**: Verify basic Markdown formatting

#### Validations:
```python
assert isinstance(content, str)
assert "#" in content  # Title formatting
assert "**" in content  # Bold text
assert not "<h1>" in content  # No HTML tags
```

### 6. Section References (`test_narrator_agent_content_formatting`)
**Purpose**: Test section reference formatting

#### Test Content:
```markdown
Un titre simple

Un paragraphe avec du texte en *italique* et quelques mots importants.

1. Premier choix - aller à la section 3
2. Deuxième choix - aller à la section 4
3. Troisième choix - aller à la section 5
```

#### Validations:
```python
assert "[[3]]" in content and "[[4]]" in content and "[[5]]" in content
```

### 7. Section Selection (`test_narrator_section_selection`)
**Purpose**: Test basic section loading functionality

#### Validations:
```python
assert "state" in result
assert "content" in result["state"]
assert result["state"]["source"] in ["loaded", "cache"]
```

## Content Processing
1. Load Phase:
   - Check for cached content
   - Load from source if no cache exists
   - Content reading with proper encoding
2. Format Phase:
   - Markdown formatting (titles, bold text)
   - Section reference formatting [[X]]
   - Maintaining engaging narrative style
3. Cache Phase:
   - Automatic cache management
   - Source tracking (loaded/cache)

## Error Handling
- Missing sections
- Invalid inputs
- Section not found
- Clear error messages

## Best Practices
- UTF-8 encoding for all files
- Explicit section numbering
- Clear separation of content and formatting
- Robust cache management
- Comprehensive error reporting
