# Decision Agent

The Decision Agent is responsible for interpreting user responses and making game flow decisions based on rules and current game state.

## Core Responsibilities

- Analyzing user responses
- Validating choices against rules
- Managing game flow decisions
- Handling conditional logic
- Coordinating with Rules Agent

## Implementation

The Decision Agent is implemented through the `DecisionAgent` class which implements the `DecisionAgentProtocol`:

```python
class DecisionAgent(BaseAgent, DecisionAgentProtocol):
    """Agent responsible for decision-making."""
    
    async def analyze_decision(self, state: GameState) -> GameState:
        """
        Analyze user decisions and validate against rules.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated game state with decision analysis
        """
```

## Decision Analysis Process

1. **Input Processing**
   - Receives current game state
   - Extracts user response
   - Gets current section rules

2. **Response Analysis**
   ```python
   async def analyze_response(
       self,
       section_number: int,
       user_response: str,
       rules: Dict
   ) -> AnalysisResult:
   ```
   - Validates user input
   - Checks against section rules
   - Determines next actions

3. **Output Generation**
   The agent returns an `AnalysisResult` containing:
   ```json
   {
     "next_section": int,
     "conditions": ["condition1", "condition2"],
     "analysis": "Detailed analysis of the decision"
   }
   ```

## Integration

The Decision Agent works closely with:
- Rules Agent: For rule validation
- State Manager: For state updates
- Story Graph: For flow control
- Decision Manager: For decision persistence

## Configuration

The agent is configured through `DecisionAgentConfig` which includes:
- LLM model configuration
- System prompts
- Debug settings
- Dependencies (Rules Agent)

## Example Usage

```python
# Initialize Decision Agent
decision_agent = DecisionAgent(config, decision_manager)

# Analyze user decision
updated_state = await decision_agent.analyze_decision(
    current_game_state
)

# Check decision result
next_section = updated_state.next_section
if next_section:
    # Process section transition
```

## Error Handling

The Decision Agent handles various error cases:
- Invalid user responses
- Rule validation failures
- LLM processing errors
- State transition errors

## Performance Optimization

The agent implements several optimizations:
- Response caching
- Batched LLM calls
- Efficient state management
- Asynchronous processing

## Debugging Features

When debug mode is enabled:
- Detailed logging of decisions
- LLM prompt inspection
- Rule validation traces
- Performance metrics
