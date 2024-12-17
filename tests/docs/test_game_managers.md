# Test Documentation: Game Managers

## Overview
This document details the test suite for the Game Managers components, which handle state management, agent coordination, caching, and event management in the game system.

## Test Infrastructure

### Mock Components

#### State Manager Mock
**Purpose**: Simulates game state management
**Initial State Structure**:
```python
{
    'section_number': 1,
    'needs_content': True,
    'trace': {
        'stats': {
            'Caractéristiques': {
                'Habileté': 10,
                'Chance': 5,
                'Endurance': 8
            },
            'Inventaire': {
                'Objets': ['Épée', 'Bouclier']
            },
            'Ressources': {
                'Or': 100,
                'Gemme': 5
            }
        },
        'history': []
    }
}
```

#### Cache Manager
**Purpose**: Manages section content caching
**Configuration**:
- Cache directory: "test_cache"
- Implements file-based caching
- Handles cache invalidation

#### Event Manager
**Purpose**: Manages event distribution
**Features**:
- Event emission
- State updates
- Event history tracking

## Detailed Test Cases

### 1. State Manager Tests (`TestStateManager`)

#### `test_initialize_state`
**Purpose**: Verify state initialization
**Validations**:
```python
assert isinstance(state, dict)
assert state['section_number'] == 1
assert state['needs_content'] is True
assert 'trace' in state
assert 'stats' in state['trace']
```
**Specific Checks**:
- Character stats initialization
  - Habileté: 10
  - Chance: 5
  - Endurance: 8
- Inventory setup
  - Initial items: ['Épée', 'Bouclier']
- Resource tracking
  - Or: 100
  - Gemme: 5

#### `test_get_default_trace`
**Purpose**: Verify trace structure initialization
**Expected Structure**:
```python
{
    'stats': {
        'Caractéristiques': {...},
        'Inventaire': {...},
        'Ressources': {...}
    },
    'history': []
}
```
**Validations**:
- Trace dictionary structure
- Stats categories presence
- Empty history initialization

### 2. Agent Manager Tests (`TestAgentManager`)

#### `test_process_narrator_success`
**Purpose**: Test narrator processing
**Input**:
```python
initial_state = {
    "state": {
        "initial": "state"
    }
}
```
**Expected Output**:
```python
{
    "state": {
        "initial": "state",
        "current_section": {
            "content": "test content"
        }
    }
}
```
**Validations**:
- State preservation
- Content addition
- Structure integrity

#### `test_process_narrator_error`
**Purpose**: Test error handling
**Error Simulation**:
```python
mock_agents['narrator'].ainvoke.side_effect = Exception("Test error")
```
**Validations**:
- Error capture
- State preservation
- Error reporting

### 3. Cache Manager Tests (`TestCacheManager`)

#### `test_check_section_cache`
**Purpose**: Verify cache checking
**Process**:
1. Create test cache entry
2. Verify cache presence
3. Test cache retrieval
4. Validate content integrity

#### `test_get_cache_path`
**Purpose**: Test path generation
**Validations**:
- Path format
- Directory structure
- File naming convention

### 4. Event Manager Tests (`TestEventManager`)

#### `test_emit_game_event`
**Purpose**: Test event emission
**Event Types**:
- State updates
- User actions
- System events
**Validations**:
- Event delivery
- Data integrity
- State synchronization

#### `test_truncate_for_log`
**Purpose**: Test log management
**Features**:
- Log size control
- Content preservation
- Format consistency

## Configuration Details
- Uses pytest-asyncio for async testing
- Implements comprehensive mocking
- Maintains isolated test environment
- Simulates full game state cycle

## Error Handling
- Tests all error scenarios
- Validates error propagation
- Ensures system stability
- Maintains state consistency
