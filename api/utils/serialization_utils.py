"""
Utilities for serializing game state and other objects.
"""
from typing import Dict, Any
from datetime import datetime
from models.game_state import GameState

def _json_serial(obj: Any) -> Any:
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    return str(obj)

def from_game_state(state: GameState) -> Dict[str, Any]:
    """
    Convert a GameState to a serializable dictionary.
    """
    try:
        data = state.model_dump()
        
        # Convertir les datetime en str
        if isinstance(data.get('state'), dict):
            for key, value in data['state'].items():
                if isinstance(value, datetime):
                    data['state'][key] = _json_serial(value)
                elif isinstance(value, dict):
                    for k, v in value.items():
                        if isinstance(v, datetime):
                            value[k] = _json_serial(v)
        
        return data
    except Exception as e:
        # Fallback en cas d'erreur
        return {
            "session_id": state.session_id,
            "game_id": state.game_id,
            "state": state.state if not isinstance(state.state, dict) or "state" not in state.state else {
                k: _json_serial(v) for k, v in state.state.items() if k != "state"
            }
        }
