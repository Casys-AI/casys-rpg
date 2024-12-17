# Test Documentation: Event Bus

## Overview
This document details the test suite for the Event Bus component, which provides event-driven communication between different parts of the game system.

## Test Infrastructure

### Fixtures
- `event_bus`: Fresh EventBus instance for each test
- Implements async/await patterns
- Maintains isolated test environment

## Detailed Test Cases

### 1. Basic Subscribe and Emit (`test_subscribe_and_emit`)
**Purpose**: Verify core event functionality

#### Test Implementation:
```python
received_data = []

async def listener(event):
    received_data.append(event.data)

await event_bus.subscribe("test_event", listener)
await event_bus.emit(Event(
    type="test_event", 
    data={"message": "test"}
))
```

#### Validations:
```python
assert len(received_data) == 1
assert received_data[0]["message"] == "test"
```

### 2. Multiple Listeners (`test_multiple_listeners`)
**Purpose**: Test multi-subscriber support

#### Test Setup:
```python
count1 = []
count2 = []

async def listener1(event):
    count1.append(event.data)

async def listener2(event):
    count2.append(event.data)
```

#### Event Distribution:
```python
await event_bus.subscribe("test_event", listener1)
await event_bus.subscribe("test_event", listener2)
await event_bus.emit(Event(type="test_event", data="data"))
```

#### Validations:
```python
assert len(count1) == len(count2) == 1
```

### 3. Event History (`test_event_history`)
**Purpose**: Verify event tracking

#### Test Sequence:
```python
await event_bus.emit(Event(type="event1", data="data1"))
await event_bus.emit(Event(type="event2", data="data2"))
```

#### History Validation:
```python
assert len(history) == 2
assert history[0].type == "event1"
assert history[1].type == "event2"
```

### 4. Error Handling (`test_error_handling`)
**Purpose**: Test system resilience

#### Error Simulation:
```python
async def faulty_listener(event):
    raise Exception("Test error")

await event_bus.subscribe("error_event", faulty_listener)
await event_bus.emit(Event(type="error_event", data="data"))
```

#### Validations:
- Exception containment
- System stability
- Event delivery continuation

### 5. Game Event Sequence (`test_game_event_sequence`)
**Purpose**: Test game-specific events

#### Event Types:
- dice_roll
- content_update
- stats_update

#### Test Implementation:
```python
events_sequence = []

async def game_listener(event):
    events_sequence.append(event.type)

# Subscribe to all game events
for event_type in ["dice_roll", "content_update", "stats_update"]:
    await event_bus.subscribe(event_type, game_listener)

# Emit sequence
await event_bus.emit(Event(type="dice_roll", data={"result": 6}))
await event_bus.emit(Event(type="content_update", data={"section": 1}))
await event_bus.emit(Event(type="stats_update", data={"health": 10}))
```

#### Sequence Validation:
```python
assert events_sequence == [
    "dice_roll",
    "content_update",
    "stats_update"
]
assert len(event_bus.history) == 3
```

### 6. Event Filtering (`test_event_filtering`)
**Purpose**: Test event type isolation

#### Filter Setup:
```python
dice_events = []
content_events = []

async def dice_listener(event):
    dice_events.append(event)

async def content_listener(event):
    content_events.append(event)
```

#### Validation:
```python
assert len(dice_events) == 1
assert len(content_events) == 1
assert dice_events[0].data["result"] == 6
assert content_events[0].data["section"] == 1
```

### 7. Concurrent Events (`test_concurrent_events`)
**Purpose**: Test async event handling

#### Implementation:
```python
processed_events = []

async def slow_listener(event):
    await asyncio.sleep(0.1)
    processed_events.append(event.type)

events = [Event(type="concurrent_test", data={"id": i}) 
         for i in range(3)]
await asyncio.gather(*[event_bus.emit(event) for event in events])
```

#### Validations:
```python
assert len(processed_events) == 3
assert len(event_bus.history) == 3
```

### 8. Event Data Integrity (`test_event_data_integrity`)
**Purpose**: Verify data preservation

#### Test Data:
```python
complex_data = {
    "stats": {"strength": 10, "agility": 8},
    "inventory": ["sword", "shield"],
    "position": {"x": 100, "y": 200}
}
```

#### Validations:
```python
assert received_data["stats"]["strength"] == 10
assert received_data["inventory"] == ["sword", "shield"]
assert received_data["position"]["x"] == 100
```

## Event Types
1. Game Events:
   - dice_roll
   - content_update
   - stats_update
2. System Events:
   - error
   - state_update
3. User Events:
   - user_input
   - decision

## Best Practices
- Async event handling
- Error isolation
- Event type consistency
- Data integrity preservation
