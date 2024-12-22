# Rules Agent

The Rules Agent is a specialized LLM agent responsible for managing and interpreting game rules. It uses RAG (Retrieval Augmented Generation) to analyze game sections and determine applicable rules.

## Core Responsibilities

- Analyzing game section rules
- Determining dice roll requirements
- Validating player actions
- Managing game conditions
- Tracking section transitions

## Implementation

The Rules Agent is implemented through the `RulesAgent` class which implements the `RulesAgentProtocol`:

```python
class RulesAgent(BaseAgent, RulesAgentProtocol):
    """Agent responsible for rules analysis."""
    
    async def process_section_rules(
        self, 
        section_number: int, 
        content: Optional[str] = None
    ) -> RulesModel:
        """
        Process and analyze rules for a game section.
        
        Args:
            section_number: Section number
            content: Optional section content
            
        Returns:
            RulesModel: Analyzed rules with dice requirements,
                       conditions and choices
        """
```

## Rule Analysis Process

1. **Input Processing**
   - Receives section number and optional content
   - Retrieves section content if not provided

2. **Rule Extraction**
   - Uses RAG to find relevant rules
   - Analyzes section content
   - Identifies key game mechanics

3. **Output Generation**
   The agent returns a `RulesModel` containing:
   ```json
   {
     "needs_dice_roll": true|false,
     "dice_type": "chance"|"combat"|null,
     "conditions": ["condition1", "condition2"],
     "next_sections": [1, 2, 3],
     "rules_summary": "Rules summary"
   }
   ```

## Integration

The Rules Agent integrates with:
- Story Graph: For game flow management
- State Manager: For tracking game state
- Cache Manager: For rule caching
- Decision Agent: For validating choices

## Configuration

The agent is configured through `RulesAgentConfig` which includes:
- LLM model settings
- System prompts
- RAG configuration
- Debug settings

## Example Usage

```python
# Initialize Rules Agent
rules_agent = RulesAgent(config, rules_manager)

# Process section rules
rules = await rules_agent.process_section_rules(
    section_number=1,
    content="Optional section content"
)

# Check dice requirements
if rules.needs_dice_roll:
    dice_type = rules.dice_type
    # Handle dice roll
```

## Error Handling

The Rules Agent includes robust error handling for:
- Invalid section numbers
- Missing content
- RAG retrieval failures
- LLM processing errors

## Performance Considerations

- Uses caching for frequently accessed rules
- Implements batched processing for multiple rules
- Optimizes RAG queries for speed
- Manages memory usage for large rule sets
