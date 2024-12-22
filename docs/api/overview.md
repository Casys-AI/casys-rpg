# API Documentation

The Casys RPG API provides a comprehensive interface for interacting with the game engine. It supports both REST and WebSocket connections for real-time game state updates.

## API Overview

Base URL: `http://127.0.0.1:8000`

## Authentication

Currently, the API does not require authentication. However, CORS is enabled with the following configuration:
- All origins allowed (`*`)
- All methods allowed
- All headers allowed
- Credentials supported

## WebSocket Connection

### Connect to Game Updates
```
ws://127.0.0.1:8000/ws
```

WebSocket messages follow this format:
```json
{
    "type": "state_update",
    "data": {
        "section_number": 1,
        "narrative": {...},
        "rules": {...},
        "decision": {...},
        "trace": {...}
    }
}
```

## REST Endpoints

### Health Check
```http
GET /health
```

Response:
```json
{
    "status": "healthy",
    "message": "Service is running",
    "timestamp": "2024-12-22T14:00:00Z"
}
```

### Game State
```http
GET /state
```

Returns the current game state including:
- Current section
- Player status
- Game progress
- Active conditions

### Navigation
```http
POST /navigate/{section_number}
```

Navigate to a specific section with optional streaming updates.

### User Input
```http
POST /response
```

Submit user responses or decisions:
```json
{
    "response": "player response text",
    "section": 1
}
```

### Game Actions
```http
POST /action
```

Perform game actions:
```json
{
    "action_type": "dice_roll",
    "parameters": {
        "dice_type": "combat",
        "modifier": 0
    }
}
```

### Feedback
```http
POST /feedback
```

Submit player feedback:
```json
{
    "section_number": 1,
    "feedback_type": "bug",
    "content": "Feedback description",
    "timestamp": "2024-12-22T14:00:00Z"
}
```

## Response Models

### ActionResponse
```python
class ActionResponse:
    success: bool
    message: str
    state: GameState | None = None
```

### GameState
```python
class GameState:
    section_number: int
    player_input: Optional[str]
    decision: Optional[DecisionModel]
    rules: Optional[RulesModel]
    trace: Optional[TraceModel]
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 404: Not Found
- 500: Internal Server Error

Error responses follow this format:
```json
{
    "error": true,
    "message": "Error description",
    "details": {
        "error_type": "ValidationError",
        "location": "path.to.error"
    }
}
```

## Rate Limiting

Currently, no rate limiting is implemented. However, consider implementing rate limiting in production.

## Streaming Responses

Some endpoints support streaming responses using Server-Sent Events (SSE):

```http
GET /navigate/{section_number}/stream
```

Stream format:
```
event: state_update
data: {"section": 1, "content": "..."}

event: completion
data: {"status": "complete"}
```

## WebSocket Events

### Connection Events
- `connect`: Initial connection
- `disconnect`: Connection closed
- `error`: Connection error

### Game Events
- `state_update`: Game state changes
- `action_result`: Action outcomes
- `system_message`: System notifications

## Development Tools

### Swagger UI
Available at `/docs`

### ReDoc
Available at `/redoc`

## Best Practices

1. **Error Handling**
   - Always check response status codes
   - Handle WebSocket disconnections
   - Implement retry logic

2. **State Management**
   - Cache game state locally
   - Implement state reconciliation
   - Handle state conflicts

3. **Performance**
   - Use WebSocket for real-time updates
   - Implement request batching
   - Cache responses when appropriate
