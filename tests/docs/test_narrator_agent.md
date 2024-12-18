# Test Documentation: Narrator Agent

## Overview
This document details the test suite for the Narrator Agent component, which manages content loading, formatting, and presentation in the game system.

## Test Infrastructure

### Fixtures

#### `temp_dir`
**Purpose**: Creates a temporary directory for test files
```python
@pytest.fixture
def temp_dir():
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)
```

#### `cache_config`
**Purpose**: Provides configuration for the cache manager
```python
@pytest.fixture
def cache_config(temp_dir):
    return CacheManagerConfig(
        cache_dir=temp_dir,
        content_dir=os.path.join(temp_dir, "sections"),
        trace_dir=os.path.join(temp_dir, "trace")
    )
```

#### `cache_manager`
**Purpose**: Creates a cache manager instance for testing
```python
@pytest.fixture
def cache_manager(cache_config):
    return CacheManager(config=cache_config)
```

#### `narrator_config`
**Purpose**: Provides configuration for the narrator agent
```python
@pytest.fixture
def narrator_config():
    return NarratorConfig(
        model_name="gpt-4o-mini",
        temperature=0.7,
        system_message="You are a skilled narrator for an interactive game book."
    )
```

#### `mock_llm`
**Purpose**: Provides a mock LLM for testing
```python
class MockResponse:
    def __init__(self, content):
        self.content = content

@pytest.fixture
def mock_llm():
    mock = AsyncMock()
    mock.ainvoke.return_value = MockResponse("Formatted Test content")
    return mock
```

#### `narrator_agent`
**Purpose**: Creates a narrator agent instance for testing
```python
@pytest.fixture
def narrator_agent(narrator_config, cache_manager, mock_llm):
    agent = NarratorAgent(
        config=narrator_config,
        cache_manager=cache_manager
    )
    agent.llm = mock_llm
    return agent
```

## Test Cases

### 1. Content Formatting (`test_narrator_agent_format_content`)
**Purpose**: Verify that the agent correctly formats content using the LLM

#### Test Sequence:
```python
@pytest.mark.asyncio
async def test_narrator_agent_format_content(narrator_agent, mock_llm):
    raw_content = "Test content"
    mock_llm.ainvoke.return_value = MockResponse(f"# Formatted Content\n\n{raw_content}")
    formatted = await narrator_agent.format_content(raw_content)
```

#### Validations:
- Content is not None
- Content is a string
- Original content is preserved in the formatted output
- LLM is called correctly with system and human messages

### 2. Section Reading (`test_narrator_agent_read_section`)
**Purpose**: Verify section reading from source files

#### Test Sequence:
```python
@pytest.mark.asyncio
async def test_narrator_agent_read_section(narrator_agent, cache_manager, temp_dir, mock_llm):
    section = 1
    raw_content = "Test section content"
    
    # Create test section file
    os.makedirs(os.path.join(temp_dir, "sections"), exist_ok=True)
    with open(os.path.join(temp_dir, "sections", f"{section}.md"), "w") as f:
        f.write(raw_content)
```

#### Validations:
- Content is properly formatted with Markdown
- Section links are correctly formatted
- Content is cached after reading
- Source type is correctly set

### 3. Cache Reading (`test_narrator_agent_cache`)
**Purpose**: Verify reading content from cache

#### Test Sequence:
```python
@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent, cache_manager, mock_llm):
    section = 1
    cached_content = "Cached content"
    cache_section = NarratorModel(
        section_number=section,
        content=cached_content,
        source_type=SourceType.CACHED
    )
    cache_manager.save_section_to_cache(section, cache_section)
```

#### Validations:
- Cached content is retrieved correctly
- Source type is set to CACHED
- No formatting is performed on cached content

### 4. Section Not Found (`test_narrator_agent_section_not_found`)
**Purpose**: Verify handling of non-existent sections

#### Test Sequence:
```python
@pytest.mark.asyncio
async def test_narrator_agent_section_not_found(narrator_agent, mock_llm):
    section = 999  # Non-existent section
    state = GameState(
        section_number=section,
        narrative=NarratorModel(
            section_number=section,
            content="",
            source_type=SourceType.RAW
        )
    )
```

#### Validations:
- Error is properly set in the response
- "Section not found" message is included
- Error handling preserves game state

## Error Handling

The test suite verifies error handling for:
- Missing sections
- Invalid cache entries
- LLM formatting failures
- File system errors

## Mock Configuration

The test suite uses mocks for:
- LLM responses
- File system operations (when needed)
- Cache operations (when testing error cases)

## Test Coverage

The test suite covers:
- Content formatting
- Section reading
- Cache management
- Error handling
- State management
- LLM integration

## Future Improvements

Consider adding tests for:
- Concurrent section access
- Large content handling
- Network failures with LLM
- Cache invalidation
- Performance benchmarks
