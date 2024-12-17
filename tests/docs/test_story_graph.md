# Test Documentation: Story Graph

## Overview
This document details the test suite for the Story Graph component, which orchestrates the interaction between various game agents (Rules, Decision, Narrator, and Trace) to manage game flow.

## Test Infrastructure

### Mock Components

#### MockEventBus
**Purpose**: Simulates the event management system
**Capabilities**:
- State management
- Event emission simulation
- Async state updates

#### Mock Agents
Each agent has specific mock behaviors:

1. **Rules Agent Mock**
```python
{
    "state": {
        "rules": {
            "needs_dice": True,
            "dice_type": "normal",
            "conditions": [],
            "next_sections": [2],
            "rules_summary": "Test rules for section 1"
        }
    }
}
```

2. **Narrator Agent Mock**
```python
{
    "state": {
        "content": "Test content for section 1",
        "section_number": 1,
        "needs_content": False
    }
}
```

3. **Decision Agent Mock**
```python
{
    "state": {
        "decision": {
            "awaiting_action": "user_input",
            "section_number": 2
        }
    }
}
```

4. **Trace Agent Mock**
```python
{
    "state": {
        "trace": {
            "stats": {
                "Caractéristiques": {
                    "Habileté": 10,
                    "Chance": 5,
                    "Endurance": 8
                },
                "Ressources": {
                    "Or": 100
                },
                "Inventaire": {
                    "Objets": ["Épée", "Bouclier"]
                }
            },
            "history": []
        }
    }
}
```

## Detailed Test Cases

### 1. Initial State (`test_story_graph_initial_state`)
**Purpose**: Verify story graph initialization
**Validations**:
- Initial section number = 1
- Current section presence
- Content status
- Error state
**Expected Structure**:
```python
{
    "state": {
        "section_number": 1,
        "current_section": {
            "number": 1
        },
        "needs_content": False,
        "error": None
    }
}
```

### 2. User Response with Dice (`test_story_graph_user_response_with_dice`)
**Purpose**: Test dice-based decision processing
**Input State**:
```python
{
    "section_number": 1,
    "user_response": "Option 1",
    "dice_result": {
        "value": 6,
        "type": "combat"
    },
    "current_section": {
        "number": 1,
        "content": "Test content",
        "choices": ["Option 1", "Option 2"]
    }
}
```
**Validations**:
- Section number preservation
- User response recording
- Dice result integration

### 3. User Response without Dice (`test_story_graph_user_response_without_dice`)
**Purpose**: Test standard decision processing
**Input State**:
```python
{
    "section_number": 1,
    "user_response": "Option 1",
    "current_section": {
        "number": 1,
        "content": "Test content",
        "choices": ["Option 1", "Option 2"]
    }
}
```
**Validations**:
- Section state maintenance
- User response processing
- Choice validation

### 4. Error Handling (`test_story_graph_error_handling`)
**Purpose**: Verify error management
**Test Approach**:
- Simulates agent failures
- Tests error propagation
- Validates error state
**Error Simulation**:
- All agents configured to raise exceptions
- Tests system resilience
- Validates error reporting

## Configuration Details
- Uses pytest-asyncio for async testing
- Implements comprehensive mock system
- Maintains isolated test environment
- Simulates full game flow
