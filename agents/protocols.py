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
            section_number: Current section number
            player_input: Player input or dice result
            rules: Rules to apply for analysis
            
        Returns:
            Dict: Analysis result with next_section and analysis
        """
        ...
        
    async def _analyze_decision(self, state: GameState) -> Dict:
        """
        Analyze decision based on state.
        
        Args:
            state: Current state
            
        Returns:
            Dict: Decision
        """
        ...
        
    def _format_response(self, player_input: Optional[str], dice_roll: Optional[int]) -> str:
        """
        Format complete response with dice roll if present.
        
        Args:
            player_input: Optional player input
            dice_roll: Optional dice roll
            
        Returns:
            str: Formatted response
        """
        ...

@runtime_checkable
class RulesAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for rules agent."""
    
    async def process_section_rules(self, section_number: int, content: str) -> RulesModel:
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
    
    async def read_section(self, section_number: int) -> str:
        """
        Read a section from the book.
        
        Args:
            section_number: Section number to read
            
        Returns:
            str: Section content
        """
        ...
        
    async def _format_content(self, content: str) -> str:
        """
        Format section content for display.
        
        Args:
            content: Raw section content
            
        Returns:
            str: Formatted content
        """
        ...

@runtime_checkable
class StoryGraphProtocol(BaseAgentProtocol, Protocol):
    """Protocol for StoryGraph class."""
    
    async def process_section(self, section_number: int) -> NarratorModel:
        """Process a section and return its content."""
        ...
        
    async def process_user_input(self, user_input: str) -> Union[NarratorModel, None]:
        """Process user input and return next section if applicable."""
        ...

@runtime_checkable
class NarratorProtocol(BaseAgentProtocol, Protocol):
    """Protocol for narrator agent."""
    
    async def read_section(self, section_number: int, input_data: Dict) -> NarratorModel:
        """Read section content."""
        ...
        
    async def format_content(self, content: str) -> str:
        """Format content with LLM and Markdown."""
        ...

@runtime_checkable
class TraceAgentProtocol(BaseAgentProtocol, Protocol):
    """Protocol for trace agent."""
    
    async def analyze_state(self, state: GameState) -> GameState:
        """
        Analyze the current game state and make decisions.
        
        Args:
            state: Current game state
            
        Returns:
            GameState: Updated game state with decisions
        """
        ...
        
    async def get_feedback(self, state: GameState) -> str:
        """
        Get feedback about the current game state.
        
        Args:
            state: Current game state
            
        Returns:
            str: Feedback about the current state
        """
        ...

@runtime_checkable
class StoryGraphProtocol(BaseAgentProtocol, Protocol):
    """Protocol for story graph."""
    
    async def process_section(self, section_number: int) -> Dict[str, Any]:
        """
        Process a complete section through the workflow.
        
        Args:
            section_number: Section number to process
            
        Returns:
            Dict[str, Any]: Processed game state
        """
        ...
        
    async def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and update game state accordingly.
        
        Args:
            user_input: User's response or decision
            
        Returns:
            Dict[str, Any]: Updated game state
        """
        ...
