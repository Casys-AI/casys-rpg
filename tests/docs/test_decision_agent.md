# Test Documentation: Decision Agent

## Overview
This document details the test suite for the Decision Agent component, which processes user responses and makes game flow decisions based on rules and context.

## Test Infrastructure

### Mock Components

#### MockRulesAgent
**Purpose**: Simulates the Rules Agent
**Implementation**:
```python
class MockRulesAgent:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.cache = {}

    async def ainvoke(self, input_data):
        state = input_data.get("state", {})
        section = state.get("section_number", 1)
        rules = self.cache.get(section, {
            "choices": ["Option 1", "Option 2"],
            "needs_dice": False
        })
        
        await self.event_bus.emit(Event(
            type="rules_analyzed",
            data={
                "section_number": section,
                "rules": rules
            }
        ))
        
        yield {"state": state}
```

#### MockLLM
**Purpose**: Simulates language model responses
**Implementation**:
```python
class MockLLM(BaseChatModel):
    async def _agenerate(self, messages: List[BaseMessage], **kwargs):
        context = messages[1].content
        if "trésor" in context.lower() and "gauche" in context.lower():
            content = '{"analysis": "Le joueur va à gauche et trouve un trésor", "next_section": 2}'
        else:
            content = '{"analysis": "Choix de l\'option 1", "next_section": 2}'
            
        message = AIMessage(content=content)
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation])
```

### Fixtures
- `event_bus`: Event management system
- `rules_agent`: Configured rules agent mock
- `mock_llm`: Language model simulation
- `decision_agent`: Main test subject with configuration

## Detailed Test Cases

### 1. Basic Functionality (`test_decision_agent_basic`)
**Purpose**: Verify core decision processing

#### Input:
```python
{
    "state": {
        "section_number": 1,
        "user_response": "Option 1"
    }
}
```

#### Validations:
```python
assert isinstance(result, dict)
assert "state" in result
state = result["state"]
assert "next_section" in state or "error" in state
```

### 2. Rules Integration (`test_decision_agent_with_rules`)
**Purpose**: Test decision-making with predefined rules

#### Rule Setup:
```python
rules = {
    "choices": ["Option 1", "Option 2"],
    "needs_dice": False
}
rules_agent.cache[section] = rules
```

#### Input State:
```python
{
    "state": {
        "section_number": section,
        "user_response": "Option 1",
        "rules": rules
    }
}
```

#### Validations:
- State presence
- Next section determination
- Rule application

### 3. State Management (`test_decision_agent_state_handling`)
**Purpose**: Verify state tracking and updates

#### Initial State:
```python
{
    "section_number": 1,
    "user_response": "Option 1",
    "rules": {
        "choices": ["Option 1", "Option 2"],
        "next_sections": [2, 3],
        "needs_dice": False
    }
}
```

#### Validations:
```python
assert "next_section" in state
assert "analysis" in state
assert state["next_section"] in [2, 3]
assert isinstance(state["analysis"], str)
assert state["awaiting_action"] is None
```

### 4. Invalid Input (`test_decision_agent_invalid_input`)
**Purpose**: Test error handling

#### Test Cases:
1. Empty State:
```python
result = await decision_agent.invoke({
    "state": {}
})
assert "error" in result["state"]
```

### 5. Dice Handling (`test_decision_agent_dice_handling`)
**Purpose**: Test dice-based decisions

#### Rule Configuration:
```python
rules = {
    "choices": ["Option 1", "Option 2"],
    "needs_dice": True,
    "dice_type": "combat"
}
```

#### Validations:
- Dice requirement detection
- Action state management
- Rule application with dice

### 6. Narrator Integration (`test_decision_agent_after_narrator`)
**Purpose**: Test post-narration processing

#### Test Flow:
1. Section display
2. Response processing
3. State update verification

### 7. Full Sequence (`test_decision_agent_full_sequence`)
**Purpose**: Test complete interaction cycle

#### Sequence:
1. Display → Response → Dice
2. State transitions
3. Event emissions
4. Decision processing

### 8. Rules Usage (`test_decision_agent_uses_rules`)
**Purpose**: Verify rule-based decision making

#### Validation Points:
- Rule interpretation
- Decision consistency
- State updates
- Event handling

## Configuration
```python
config = DecisionConfig(
    llm=mock_llm,
    rules_agent=rules_agent,
    system_prompt="Test prompt"
)
```

## State Flow
1. Input Processing:
   - User response validation
   - Rule retrieval
   - State verification
2. Decision Making:
   - Rule application
   - Context analysis
   - Next section determination
3. State Update:
   - Decision recording
   - State transition
   - Event emission

## Error Handling
- Invalid input detection
- State validation
- Rule consistency checks
- Error propagation

## Best Practices
- State immutability
- Event-driven updates
- Error isolation
- Context preservation
