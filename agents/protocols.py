"""
Agent protocols for the game engine.
"""
from typing import Protocol, Dict, Optional, AsyncGenerator, Any, runtime_checkable, List, Union
from datetime import datetime
from models.game_state import GameState
from models.rules_model import RulesModel
from models.trace_model import TraceModel
from models.character_model import CharacterModel
from models.decision_model import DecisionModel
from models.narrator_model import NarratorModel

@runtime_checkable
class BaseAgentProtocol(Protocol):
    """Base protocol for all agents."""
    
    async def ainvoke(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronous invocation of the agent.
        
        Args:
            input_data (Dict[str, Any]): Input data for the agent
            
        Returns:
            AsyncGenerator[Dict[str, Any], None]: Generator yielding updated states
        """
        ...

@runtime_checkable
class AgentManagerProtocol(Protocol):
    """Protocol for agent manager."""
    
    async def initialize_game_session(self) -> None:
        """Initialize a new game session."""
        ...
    
    async def get_current_game_state(self) -> GameState:
        """Get the current state of the game."""
        ...
    
    async def stream_game_updates(self) -> AsyncGenerator[GameState, None]:
        """Stream game state updates."""
        ...
    
    async def handle_user_section_request(self, section_number: int) -> GameState:
        """Process a user's request to move to a specific section."""
        ...
    
    async def handle_user_response(self, response: str) -> GameState:
        """Process a user's response or decision."""
        ...
    
    async def handle_user_action(self, action: Dict[str, Any]) -> GameState:
        """Process a user's game action."""
        ...
    
    def create_error_response(self, error: str) -> GameState:
        """Create an error state response."""
        ...
    
    async def get_user_feedback(self) -> str:
        """Get feedback about the current game state."""
        ...

@runtime_checkable
class StoryGraphProtocol(Protocol):
    """Protocol for story graph."""
    
    async def start_session(self) -> None:
        ...
    
    async def execute_game_workflow(self, state: GameState) -> GameState:
        """Execute the main game workflow for a given state."""
        ...
    
    async def validate_state_transition(self, from_state: GameState, to_state: GameState) -> bool:
        """Validate if a state transition is legal."""
        ...
    
    async def process_game_section(self, section_number: int) -> GameState:
        """Process a complete game section."""
        ...
    
    async def apply_section_rules(self, state: GameState) -> GameState:
        """Apply game rules to the current state."""
        ...
    
    async def merge_agent_results(self, results: Dict[str, Any]) -> GameState:
        """Merge results from multiple agents into a single state."""
        ...
    
    async def _process_workflow(self, state: Dict, stream: bool = False) -> Union[Dict, AsyncGenerator[Dict, None]]:
        ...
    
    async def stream_game_state(self) -> AsyncGenerator[Dict, None]:
        ...
    
    async def _process_narrative(self, state: Dict) -> Dict:
        ...
    
    async def _process_rules(self, state: Dict) -> Dict:
        ...
    
    async def _process_decision(self, state: Dict) -> Dict:
        ...
    
    async def _process_trace(self, state: Dict) -> Dict:
        ...

@runtime_checkable
class DecisionAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for decision agent."""
    
    async def invoke(self, input_data: Dict) -> Dict[str, GameState]:
        """
        Main method called by the graph.
        
        Args:
            input_data (Dict): Dictionary containing the state
            
        Returns:
            Dict[str, GameState]: Updated state with validated decision
        """
        ...
        
    async def _analyze_response(
        self, section_number: int, player_input: str, rules: Dict = None
    ) -> Dict:
        """
        Analyze player response with LLM considering rules.
        
        Args:
            section_number: Section number
            player_input: Player's response text
            rules: Optional rules to consider
            
        Returns:
            Dict: Analysis results
        """
        ...

@runtime_checkable
class RulesAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for rules agent."""
    
    async def process_section_rules(
        self, section_number: int, content: str
    ) -> RulesModel:
        """
        Process and analyze rules for a game section.
        
        Args:
            section_number: Section number to analyze
            content: Section content
            
        Returns:
            RulesModel: Analyzed rules with dice requirements, conditions and choices
        """
        ...

@runtime_checkable
class NarratorAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for narrator agent."""
    
    async def read_section(self, section_number: int) -> NarratorModel:
        """
        Read a section from the book.
        
        Args:
            section_number: Section number to read
            
        Returns:
            NarratorModel: Section content and metadata
        """
        ...

@runtime_checkable
class TraceAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for trace agent."""
    
    async def analyze_state(self, state: GameState) -> TraceModel:
        """
        Analyze the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            TraceModel: Analysis results and history
        """
        ...
    
    async def get_feedback(self, state: GameState) -> str:
        """
        Get feedback about the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Feedback message
        """
        ...
