"""
Agent Manager Protocol
Defines the interface that any AgentManager implementation must follow.
"""

from typing import Dict, AsyncGenerator, Any, Protocol, runtime_checkable
from models.game_state import GameState
from config.game_config import GameConfig

@runtime_checkable
class AgentManagerProtocol(Protocol):
    """High-level coordinator for game interactions.
    Responsible for managing agent interactions and game flow."""
    
    async def initialize(self, config: GameConfig) -> None:
        """Initialize the agent manager with configuration."""
        ...
        
    async def initialize_game(self) -> None:
        """
        Start a new game session.
        This prepares the game state and initializes all components.
        Can be called multiple times to start new sessions.
        """
        ...
    
    async def get_state(self) -> GameState:
        """Get the current state of the game."""
        ...
    
    async def subscribe_to_updates(self) -> AsyncGenerator[GameState, None]:
        """Stream les mises à jour du jeu en temps réel."""
        ...
    
    async def navigate_to_section(self, section_number: int) -> GameState:
        """
        Process a user's request to move to a specific section.
        
        Args:
            section_number: The section number requested by the user
            
        Returns:
            GameState: Updated game state after processing the section
        """
        ...
    
    async def submit_response(self, response: str) -> GameState:
        """
        Process a user's response or decision.
        
        Args:
            response: The user's response or decision
            
        Returns:
            GameState: Updated game state after processing the response
        """
        ...
    
    async def perform_action(self, action: Dict[str, Any]) -> GameState:
        """
        Process a user's game action.
        
        Args:
            action: Dictionary containing action details
            
        Returns:
            GameState: Updated game state after processing the action
        """
        ...
    
    async def should_continue(self, state: GameState) -> bool:
        """
        Vérifie si le jeu doit continuer.
        
        Args:
            state: État actuel du jeu
            
        Returns:
            bool: True si le jeu doit continuer
        """
        ...
    
    async def get_user_feedback(self) -> str:
        """
        Get feedback about the current game state.
        
        Returns:
            str: Feedback message
        """
        ...
