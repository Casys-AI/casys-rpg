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

# Test content creation
test_content = "Test content for section 1"
with open(os.path.join(temp_dir, "1.md"), "w") as f:
    f.write(test_content)

with open(os.path.join(cache_dir, "1_cached.md"), "w") as f:
    f.write(test_content)
```

#### `narrator_agent`
**Configuration**:
```python
config = NarratorConfig(
    llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
    content_directory=content_dir
)
```

## Detailed Test Cases

### 1. Basic Functionality (`test_narrator_agent_basic`)
**Purpose**: Verify core content loading

#### Input:
```python
{"state": {"section_number": 1, "use_cache": False}}
```

#### Validations:
```python
assert "content" in result["state"]
assert "Test content for section 1" in result["state"]["content"]
assert result["state"]["source"] == "loaded"
```

### 2. Cache Management (`test_narrator_agent_cache`)
**Purpose**: Test caching system

#### Test Sequence:
1. First Load (No Cache):
```python
result1 = await narrator_agent.ainvoke({
    "state": {
        "section_number": 1,
        "use_cache": False
    }
})
assert result1["state"]["source"] == "loaded"
```

2. Second Load (With Cache):
```python
result2 = await narrator_agent.ainvoke({
    "state": {
        "section_number": 1,
        "use_cache": True
    }
})
assert result2["state"]["source"] == "cache"
```

### 3. Cache Directory Usage (`test_narrator_agent_cache_directory`)
**Purpose**: Verify cache prioritization

#### Directory Structure:
```
temp_dir/
├── 1.md
└── cache/
    └── 1_cached.md
```

#### Validations:
- Cache file detection
- Content consistency
- Source tracking

### 4. Invalid Input (`test_invalid_input`)
**Purpose**: Test error handling

#### Test Cases:
1. Missing Section:
```python
result = await narrator_agent.ainvoke({"state": {}})
assert "error" in result["state"]
```

2. Invalid Section:
```python
result = await narrator_agent.ainvoke({
    "state": {
        "section_number": 999,
        "use_cache": False
    }
})
assert "Content not found for section 999" in result["state"]["error"]
```

### 5. Content Format (`test_narrator_agent_content_format`)
**Purpose**: Verify HTML formatting

#### Validations:
```python
assert isinstance(content, str)
assert "<h1>" in content or "<p>" in content
```

### 6. Content Formatting (`test_narrator_agent_content_formatting`)
**Purpose**: Test markdown processing

#### Test Content:
```markdown
# Test Title

Test paragraph with *italic* text
```

#### Expected HTML:
```html
<h1>Test Title</h1>
<p>Test paragraph with <em>italic</em> text</p>
```

#### Validations:
```python
assert "<h1>" in content
assert "<em>" in content or "<i>" in content
assert "<p>" in content
```

### 7. Section Selection (`test_narrator_section_selection`)
**Purpose**: Test section loading accuracy

#### Validations:
```python
assert "state" in result
assert "content" in result["state"]
assert result["state"]["source"] in ["loaded", "cache"]
```

## File Structure
```
content_dir/
├── [section_number].md
└── cache/
    └── [section_number]_cached.md
```

## Content Processing
1. Load Phase:
   - File existence check
   - Cache verification
   - Content reading
2. Format Phase:
   - Markdown parsing
   - HTML conversion
   - Style application
3. Cache Phase:
   - Cache creation
   - Content storage
   - Source tracking

## Error Handling
- Missing files
- Invalid sections
- Format errors
- Cache failures

## Best Practices
- Cache management
- Content validation
- Format consistency
- Error reporting
