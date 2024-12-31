# Test Patterns and Common Pitfalls

## Model Testing Patterns

### State Model Testing

#### Required Fields Pattern
When testing state models (like GameState), always remember:
```python
# BAD - Missing required fields
GameState(section_number=1)  # Will raise ValidationError

# GOOD - Include all required fields
GameState(
    section_number=1,
    session_id=str(uuid.uuid4()),
    game_id=str(uuid.uuid4())
)
```

#### Immutable State Pattern
For state models that support immutable operations:
```python
# BAD - Modifying state directly
state.section_number = 2  # Will raise AttributeError

# GOOD - Using immutable operations
new_state = state.with_updates(section_number=2)
# or
new_state = state + other_state  # Using defined operators
```

### Mock Testing Patterns

#### Protocol-Based Mocking
When mocking managers or agents:
```python
# BAD - Importing concrete implementation
from managers.workflow_manager import WorkflowManager
mock = AsyncMock(spec=WorkflowManager)

# GOOD - Using protocol
from managers.protocols.workflow_manager_protocol import WorkflowManagerProtocol
mock = AsyncMock(spec=WorkflowManagerProtocol)
```

#### Fixture Chain Pattern
When fixtures depend on each other:
```python
# BAD - Creating dependencies inside fixture
@pytest.fixture
def workflow_manager():
    state_manager = StateManager()  # Direct instantiation
    return WorkflowManager(state_manager)

# GOOD - Injecting dependencies
@pytest.fixture
def state_manager():
    return AsyncMock(spec=StateManagerProtocol)

@pytest.fixture
def workflow_manager(state_manager):  # Dependency injection
    return WorkflowManager(state_manager)
```

## Common Pitfalls

### Circular Import Issues

#### Problem
```python
# managers/workflow_manager.py
from agents.story_graph import StoryGraph  # Direct import

# agents/story_graph.py
from managers.workflow_manager import WorkflowManager  # Circular!
```

#### Solution
1. Use protocols instead of concrete implementations
2. Move imports into TYPE_CHECKING block when possible
3. Consider restructuring component dependencies

### Async Testing Issues

#### Problem
```python
# BAD - Mixing sync and async
@pytest.fixture
def state_manager():
    manager = AsyncMock()
    manager.get_state = lambda: GameState()  # Sync function!
    return manager
```

#### Solution
```python
# GOOD - Consistent async usage
@pytest.fixture
def state_manager():
    manager = AsyncMock()
    manager.get_state = AsyncMock(return_value=GameState(...))
    return manager
```

## Testing Complex Workflows

### Story Graph Testing Pattern
For testing components that combine multiple managers and agents:

```python
@pytest.fixture
def story_graph(managers_dict, agents_dict):
    """Create story graph with all dependencies injected."""
    return StoryGraph(
        managers=managers_dict,  # Dictionary of manager mocks
        agents=agents_dict,      # Dictionary of agent mocks
        config=mock_config       # Configuration mock
    )
```

### Factory Testing Pattern
For testing factory classes that create multiple components:

```python
@pytest.fixture
def game_factory():
    """Create factory with mocked config."""
    config = GameConfig(
        manager_configs=ManagerConfigs(
            storage_config=StorageConfig(...)
        ),
        agent_configs=AgentConfigs(...)
    )
    return GameFactory(config)
```

## Best Practices for CASYS RPG Testing

1. **Always Use Protocols**: Test against protocols, not implementations
2. **Mock at Protocol Level**: Create mocks based on protocols
3. **Immutable State**: Use immutable operations for state changes
4. **Dependency Injection**: Inject dependencies through fixtures
5. **Async Consistency**: Keep async/await usage consistent
6. **Configuration-Based**: Use configuration objects for setup
7. **Dictionary-Based Injection**: Use dictionaries for complex dependencies
8. **Validate Required Fields**: Always provide required fields in models
9. **Test Both Paths**: Test both success and error cases
10. **Keep Tests Isolated**: Avoid shared mutable state
