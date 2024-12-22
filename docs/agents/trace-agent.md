# Trace Agent

The Trace Agent is responsible for tracking and analyzing game state changes throughout the player's journey. It provides insights about player decisions and maintains a detailed history of the game session.

## Core Responsibilities

- Recording game state changes
- Analyzing player decisions
- Tracking game progression
- Generating player feedback
- Managing game history

## Implementation

The Trace Agent is implemented through the `TraceAgent` class which implements the `TraceAgentProtocol`:

```python
class TraceAgent(BaseAgent, TraceAgentProtocol):
    """
    Handles game state tracking and analysis.
    This agent is responsible for:
    1. Recording and analyzing game state changes
    2. Providing insights about player decisions
    3. Tracking game progression
    4. Generating feedback on player actions
    """
```

## State Tracking Process

1. **Action Creation**
   ```python
   def _create_action_from_state(self, state: GameState) -> Dict[str, Any]:
       """Create action entry from game state."""
   ```
   - Timestamps each action
   - Determines action type
   - Captures relevant details

2. **Action Types**
   The agent recognizes several types of actions:
   - `dice_roll`: Dice rolling events
   - `user_input`: Player responses
   - `decision`: Game decisions
   - `state_change`: General state updates

3. **Detail Recording**
   For each action type, specific details are captured:
   ```python
   {
     "timestamp": "ISO timestamp",
     "section": "current_section",
     "action_type": "type",
     "details": {
       "section_number": int,
       "dice_type": str,
       "result": int,
       "response": str,
       "conditions": list,
       ...
     }
   }
   ```

## State Analysis

The agent provides several analysis features:
- Action pattern recognition
- Decision impact analysis
- Progress tracking
- Player behavior insights

## Integration

The Trace Agent works with:
- State Manager: For state updates
- Character Manager: For character progression
- Decision Agent: For decision tracking
- Rules Agent: For rule compliance

## Configuration

The agent is configured through `TraceAgentConfig` which includes:
- Storage settings
- Analysis parameters
- Feedback configuration
- Debug options

## Example Usage

```python
# Initialize Trace Agent
trace_agent = TraceAgent(config, trace_manager)

# Record state
trace = await trace_agent.record_state(current_state)

# Analyze state
analyzed_state = await trace_agent.analyze_state(current_state)

# Get insights
insights = analyzed_state.trace.insights
```

## Error Handling

The agent handles various scenarios:
- State recording failures
- Analysis errors
- Storage issues
- Invalid state data

## Performance Features

- Efficient state storage
- Optimized analysis
- Batch processing
- Caching mechanisms

## Debug Features

When debug mode is enabled:
- Detailed action logging
- State change tracking
- Analysis metrics
- Error tracing

## Data Models

### TraceModel
```python
class TraceModel:
    timestamp: datetime
    actions: List[Dict[str, Any]]
    insights: Optional[Dict[str, Any]]
    feedback: Optional[str]
```

### Action Details
```python
class ActionDetails:
    section_number: int
    timestamp: str
    dice_type: Optional[str]
    result: Optional[int]
    response: Optional[str]
    conditions: List[str]
```
