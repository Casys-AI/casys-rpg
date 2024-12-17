# Test Documentation: Trace Agent

## Overview
This document details the test suite for the Trace Agent component, which manages game history recording and character statistics tracking.

## Test Infrastructure

### Fixtures
- `event_bus`: Event management system
- `trace_directory`: Temporary directory for trace storage
- `trace_agent`: Configured trace agent instance with gpt-4o-mini model

## Detailed Test Cases

### 1. Decision Recording (`test_record_decision`)
**Purpose**: Verify decision history recording
**Input State**:
```python
{
    "state": {
        "section_number": 1,
        "decision": {
            "next_section": 2,
            "awaiting_action": True,
            "conditions": ["needs_dice_roll"],
            "rules_summary": "Un jet de dé est nécessaire"
        },
        "rules": {
            "needs_dice": True,
            "dice_type": "combat"
        },
        "user_response": "Je vais à gauche"
    }
}
```
**Validations**:
- History entry creation
- Timestamp presence
- Section tracking
- Decision details recording
- File persistence

### 2. Dice Roll Recording (`test_record_dice_roll`)
**Purpose**: Test dice roll history tracking
**Input Data**:
```python
{
    "state": {
        "section_number": 1,
        "dice_result": {
            "type": "combat",
            "value": 6,
            "success": True
        }
    }
}
```
**Validations**:
- Dice roll entry creation
- Result recording
- State structure
- History update

### 3. Action Sequence (`test_multiple_actions_sequence`)
**Purpose**: Verify complete action sequence recording
**Test Sequence**:
1. Initial Decision:
   - Awaiting user input
   - No next section
2. User Response:
   - Records user choice
   - Triggers dice requirement
3. Dice Roll:
   - Records roll result
   - Finalizes sequence
**Validations**:
- Sequence integrity
- Action order
- Section consistency
- File persistence
- Complete history structure

### 4. Stats Management (`test_update_stats`)
**Purpose**: Test character statistics management
**Test Process**:
1. Initial Stats:
```python
{
    "Caractéristiques": {
        "Habileté": 10,
        "Endurance": 20
    }
}
```
2. Update:
```python
{
    "Caractéristiques": {
        "Habileté": 12
    }
}
```
**Validations**:
- Stat updates
- Unchanged value preservation
- File persistence
- Memory state

### 5. Stats Persistence (`test_stats_persistence`)
**Purpose**: Verify statistics storage
**Validations**:
- File creation
- Data persistence
- Reload accuracy
- State consistency

### 6. Stats Initialization (`test_adventure_stats_initialization`)
**Purpose**: Test initial stats setup
**Validations**:
- Default values
- Structure creation
- File initialization

### 7. Recursive Stats Update (`test_update_stats_recursive`)
**Purpose**: Test nested statistics updates
**Validations**:
- Deep updates
- Structure preservation
- Nested value integrity

### 8. Stats Retrieval (`test_get_stats`)
**Purpose**: Test statistics access
**Validations**:
- Complete stats retrieval
- Structure integrity
- Value accuracy

### 9. Stats Event Emission (`test_stats_event_emission`)
**Purpose**: Verify event system integration
**Validations**:
- Event emission
- Update notifications
- Event data accuracy

## File Structure
- `history.json`: Action history storage
- `adventure_stats.json`: Character statistics storage

## Configuration Details
- Model: gpt-4o-mini
- Uses temporary test directories
- JSON-based storage
- Event-driven updates
