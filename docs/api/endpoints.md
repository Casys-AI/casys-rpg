# API Endpoints

Detailed documentation of all available API endpoints in the Casys RPG system.

## WebSocket Endpoint

### Game State Updates
`ws://127.0.0.1:8000/ws`

Provides real-time game state updates.

**Events:**
```json
{
    "type": "state_update",
    "data": {
        "section_number": 1,
        "narrative": {
            "content": "Section text",
            "choices": ["Choice 1", "Choice 2"]
        },
        "rules": {
            "needs_dice_roll": true,
            "dice_type": "combat"
        }
    }
}
```

## REST Endpoints

### Health Check

`GET /health`

Check API health status.

**Response:**
```json
{
    "status": "healthy",
    "message": "Service is running",
    "timestamp": "2024-12-22T14:00:00Z"
}
```

**Status Codes:**
- 200: Service healthy
- 503: Service unavailable

### Game State

#### Get Current State
`GET /state`

Retrieve current game state.

**Response:**
```json
{
    "success": true,
    "state": {
        "section_number": 1,
        "player_input": null,
        "decision": {
            "section_number": 1,
            "analysis": "Decision analysis"
        },
        "rules": {
            "needs_dice_roll": false,
            "conditions": []
        },
        "trace": {
            "timestamp": "2024-12-22T14:00:00Z",
            "actions": []
        }
    }
}
```

#### Navigate to Section
`POST /navigate/{section_number}`

Navigate to a specific section.

**Parameters:**
- `section_number`: Target section number

**Response:**
```json
{
    "success": true,
    "message": "Navigation successful",
    "state": {
        "section_number": 2,
        "narrative": {
            "content": "New section content"
        }
    }
}
```

### User Input

#### Submit Response
`POST /response`

Submit user response or decision.

**Request:**
```json
{
    "response": "Player choice text",
    "section": 1
}
```

**Response:**
```json
{
    "success": true,
    "message": "Response processed",
    "state": {
        "section_number": 1,
        "decision": {
            "valid": true,
            "next_section": 2
        }
    }
}
```

### Game Actions

#### Perform Action
`POST /action`

Perform a game action.

**Request:**
```json
{
    "action_type": "dice_roll",
    "parameters": {
        "dice_type": "combat",
        "modifier": 0
    }
}
```

**Response:**
```json
{
    "success": true,
    "message": "Action completed",
    "result": {
        "dice_roll": 15,
        "modified_result": 15,
        "outcome": "success"
    }
}
```

#### Roll Dice
`POST /dice/{dice_type}`

Perform a dice roll.

**Parameters:**
- `dice_type`: Type of dice roll (combat/chance)

**Response:**
```json
{
    "success": true,
    "roll": {
        "value": 15,
        "type": "combat",
        "timestamp": "2024-12-22T14:00:00Z"
    }
}
```

### Feedback

#### Submit Feedback
`POST /feedback`

Submit player feedback.

**Request:**
```json
{
    "section_number": 1,
    "feedback_type": "bug",
    "content": "Feedback description",
    "timestamp": "2024-12-22T14:00:00Z"
}
```

**Response:**
```json
{
    "success": true,
    "message": "Feedback received",
    "feedback_id": "f12345"
}
```

#### Get Feedback
`GET /feedback`

Get feedback for current state.

**Response:**
```json
{
    "success": true,
    "feedback": {
        "suggestions": ["Suggestion 1", "Suggestion 2"],
        "warnings": [],
        "tips": ["Tip 1"]
    }
}
```

## Error Responses

All endpoints may return error responses in this format:

```json
{
    "error": true,
    "message": "Error description",
    "details": {
        "error_type": "ValidationError",
        "location": "path.to.error",
        "suggestion": "How to fix"
    }
}
```

**Common Status Codes:**
- 400: Bad Request
- 404: Not Found
- 422: Validation Error
- 500: Internal Server Error

## Streaming Endpoints

### Stream Section Navigation
`GET /navigate/{section_number}/stream`

Stream section navigation updates.

**Events:**
```
event: state_update
data: {"section": 1, "content": "..."}

event: decision
data: {"choices": ["Choice 1", "Choice 2"]}

event: completion
data: {"status": "complete"}
```

### Stream Game Updates
`GET /updates/stream`

Stream general game updates.

**Events:**
```
event: state_change
data: {"type": "dice_roll", "result": 15}

event: narrative_update
data: {"content": "New narrative content"}
```

## Headers

All endpoints accept and may require these headers:

```http
Content-Type: application/json
Accept: application/json
```

## Rate Limits

Currently no rate limits are enforced, but consider these guidelines:
- WebSocket: 1 connection per client
- REST: Max 60 requests per minute
- Streaming: 1 stream per client
