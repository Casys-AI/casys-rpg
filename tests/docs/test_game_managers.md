# Test Documentation: Game Managers

## Overview
This document details the test suite for the game management components, including state management, agent coordination, caching, and event handling.

## Test Infrastructure

### Fixtures

#### `event_bus`
**Purpose**: Mock EventBus for testing event emission and state updates
```python
mock = Mock(spec=EventBus)
mock.emit = AsyncMock()
mock.update_state = AsyncMock()
mock.get_state = AsyncMock()
```

#### `state_manager`
**Purpose**: Mock StateManager with initial game state
```python
initial_state = {
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

#### `mock_agents`
**Purpose**: Mock agent implementations for testing
- **Narrator**: Content loading and formatting
- **Rules**: Game rules processing
- **Decision**: Choice handling
- **Trace**: History tracking

## Test Cases

### StateManager Tests

#### 1. State Initialization (`test_initialize_state`)
**Purpose**: Verify correct initial game state setup

**Validations**:
```python
assert state['section_number'] == 1
assert state['needs_content'] is True
assert 'Caractéristiques' in stats
assert stats['Caractéristiques']['Habileté'] == 10
assert 'Épée' in stats['Inventaire']['Objets']
```

#### 2. Default Trace (`test_get_default_trace`)
**Purpose**: Verify correct trace structure initialization

**Validations**:
```python
assert 'stats' in trace
assert 'history' in trace
assert isinstance(trace['history'], list)
```

### AgentManager Tests

#### 1. Narrator Processing Success (`test_process_narrator_success`)
**Purpose**: Test successful content processing by narrator agent

**Test Flow**:
1. Configure mock narrator response
2. Process initial state
3. Verify content update

**Validations**:
```python
assert result["state"]["initial"] == "state"
assert result["state"]["current_section"]["content"] == "test content"
```

#### 2. Narrator Processing Error (`test_process_narrator_error`)
**Purpose**: Test error handling in narrator processing

**Test Flow**:
1. Configure mock to raise exception
2. Verify exception handling

#### 3. Rules Processing (`test_process_rules`)
**Purpose**: Test game rules application

**Expected Rules Structure**:
```python
{
    "needs_dice": True,
    "dice_type": None,
    "conditions": [],
    "next_sections": [],
    "rules_summary": None,
    "choices": []
}
```

#### 4. Decision Processing (`test_process_decision`)
**Purpose**: Test choice handling and validation

**Expected Decision Structure**:
```python
{
    "choice": "A",
    "awaiting_action": "choice"
}
```

### CacheManager Tests

#### 1. Cache Checking (`test_check_section_cache`)
**Purpose**: Verify cache existence checking

**Test Flow**:
1. Setup test cache directory
2. Check cache existence
3. Cleanup test environment

#### 2. Cache Path Generation (`test_get_cache_path`)
**Purpose**: Verify correct cache file path generation

### EventManager Tests

#### 1. Game Event Emission (`test_emit_game_event`)
**Purpose**: Test event broadcasting to event bus

**Test Flow**:
1. Create game event
2. Emit event
3. Verify event bus interaction

#### 2. Log Truncation (`test_truncate_for_log`)
**Purpose**: Test log message formatting

## Component Interactions

### State Flow
1. State initialization by StateManager
2. State updates through AgentManager
3. State persistence in cache
4. State broadcasting via EventManager

### Agent Coordination
1. Narrator processes content
2. Rules evaluate game logic
3. Decision handles user choices
4. Trace records game history

## Error Handling
- Invalid state handling
- Agent processing errors
- Cache access failures
- Event emission errors

## Best Practices
- Mock all external dependencies
- Use async/await for asynchronous operations
- Clean up test resources
- Verify component interactions
- Test both success and error cases
