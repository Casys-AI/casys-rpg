# Narrator Agent

The Narrator Agent is responsible for processing and presenting game content to the player. It handles content formatting, caching, and presentation logic.

## Core Responsibilities

- Processing game sections
- Formatting content
- Managing content caching
- Handling presentation logic
- Error management

## Implementation

The Narrator Agent is implemented through the `NarratorAgent` class which implements the `NarratorAgentProtocol`:

```python
class NarratorAgent(BaseAgent, NarratorAgentProtocol):
    """Agent responsible for content processing and presentation."""
    
    async def process_section(
        self, 
        section_number: int, 
        raw_content: Optional[str] = None
    ) -> Union[NarratorModel, NarratorError]:
        """
        Process and format a section.
        
        Args:
            section_number: Section number to process
            raw_content: Optional raw content to process
            
        Returns:
            Union[NarratorModel, NarratorError]: Processed section or error
        """
```

## Content Processing Flow

1. **Cache Check**
   - Checks for existing processed content
   - Returns cached content if available

2. **Content Retrieval**
   - Gets raw content if not provided
   - Handles missing section errors

3. **Content Formatting**
   ```python
   async def _format_content(
       self, 
       section_number: int, 
       content: str
   ) -> NarratorModel:
   ```
   - Uses LLM for content formatting
   - Applies presentation rules
   - Handles formatting errors

4. **Cache Management**
   - Saves processed content
   - Manages cache updates
   - Handles cache errors

## Output Model

The agent returns a `NarratorModel` containing:
```python
class NarratorModel:
    section_number: int
    content: str
    error: Optional[str]
    source_type: SourceType
    timestamp: datetime
```

## Integration

The Narrator Agent works with:
- Story Graph: For content flow
- Cache Manager: For content caching
- State Manager: For game state
- Narrator Manager: For content persistence

## Configuration

The agent is configured through `NarratorAgentConfig` which includes:
- LLM model settings
- System prompts
- Caching configuration
- Debug settings

## Example Usage

```python
# Initialize Narrator Agent
narrator_agent = NarratorAgent(config, narrator_manager)

# Process a section
result = await narrator_agent.process_section(
    section_number=1,
    raw_content="Optional raw content"
)

if isinstance(result, NarratorModel):
    # Present content to user
    formatted_content = result.content
else:
    # Handle error
    error_message = result.message
```

## Error Handling

The agent handles various error cases:
- Missing sections
- Formatting failures
- Cache errors
- LLM processing errors

## Performance Features

- Content caching
- Async processing
- Batched LLM calls
- Efficient error handling

## Debug Features

When debug mode is enabled:
- Content processing logs
- Cache operation tracking
- LLM interaction logging
- Performance metrics
