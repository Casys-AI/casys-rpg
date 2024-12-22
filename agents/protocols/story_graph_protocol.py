"""
Story Graph Protocol Module
Defines the interface for the Story Graph
"""

from typing import Dict, Optional, AsyncGenerator, Protocol, Any
from models.game_state import GameState
from agents.protocols.base_agent_protocol import BaseAgentProtocol

class StoryGraphProtocol(BaseAgentProtocol, Protocol):
    """Protocol defining the interface for the Story Graph."""
    
    async def process_state(self, state: GameState) -> AsyncGenerator[GameState, None]:
        """
        Process game state through the agent pipeline.
        
        Args:
            state: Current game state
            
        Yields:
            GameState: Updated game state after processing
        """
        ...
        
    async def process_section(self, section_number: int, current_state: Dict[str, Any]) -> GameState:
        """
        Process a specific game section.
        
        Args:
            section_number: Section number to process
            current_state: Current game state
            
        Returns:
            GameState: Updated game state after processing section
        """
        ...
        
    async def process_action(self, action: Dict[str, Any], current_state: GameState) -> GameState:
        """
        Process a game action.
        
        Args:
            action: Action to process
            current_state: Current game state
            
        Returns:
            GameState: Updated game state after processing action
        """
        ...
        
    async def process_user_input(self, input_data: Dict[str, Any]) -> GameState:
        """
        Process user input or decision.
        
        Args:
            input_data: User input data
            
        Returns:
            GameState: Updated game state after processing input
        """
        ...
        
    def get_agent(self, agent_type: str) -> Optional[Any]:
        """
        Get agent instance by type.
        
        Args:
            agent_type: Type of agent to retrieve
            
        Returns:
            Optional[Any]: Agent instance if found
        """
        ...
        
    async def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Handle events between agents.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        ...
        
    async def start_session(self) -> None:
        """Start a new game session."""
        ...
        
    async def stream_game_state(self) -> AsyncGenerator[GameState, None]:
        """
        Stream game state updates.
        
        Yields:
            GameState: Updated game states
        """
        ...
