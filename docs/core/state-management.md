# State Management

This document explains how state is managed in Casys RPG.

## Overview

Casys RPG uses a robust state management system to track:
- Game progression
- Character stats
- Inventory
- Game world state
- Player decisions

## State Structure

```python
@dataclass
class GameState:
    section: int
    character: CharacterState
    inventory: InventoryState
    world_state: WorldState
    decision_history: List[Decision]
```

## Storage Backend

The state management system uses Redis for:
- Fast access
- Persistence
- State recovery
- Real-time updates

## State Operations

### Save State

```python
async def save_state(state: GameState) -> bool:
    """Save current game state to Redis."""
    try:
        await redis.set(f"game:{state.id}", state.json())
        return True
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return False
```

### Load State

```python
async def load_state(state_id: str) -> GameState:
    """Load game state from Redis."""
    state_data = await redis.get(f"game:{state_id}")
    return GameState.parse_raw(state_data)
```

### Update State

```python
async def update_state(state_id: str, updates: Dict) -> GameState:
    """Update specific state attributes."""
    current_state = await load_state(state_id)
    updated_state = current_state.copy(update=updates)
    await save_state(updated_state)
    return updated_state
```

## State Recovery

The system includes mechanisms for:
- Automatic state backups
- State recovery points
- Error recovery
- State rollback

## Optimization

State management is optimized for:
- Minimal memory usage
- Fast access patterns
- Efficient updates
- Real-time synchronization
