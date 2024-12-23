"""
Decision Manager Protocol
Defines the interface for decision management.
"""
from typing import Dict, List, Optional, Any, Protocol, runtime_checkable
from models.game_state import GameState
from models.decision_model import DecisionModel, AnalysisResult

@runtime_checkable
class DecisionManagerProtocol(Protocol):
    """Protocol for decision management."""
    
    async def analyze_response(
        self, 
        section_number: int,
        user_response: str,
        rules: Dict
    ) -> AnalysisResult:
        """
        Analyze user response with LLM.
        
        Args:
            section_number: Current section number
            user_response: User's response or dice result
            rules: Rules to apply
            
        Returns:
            AnalysisResult: Analysis result with next section and conditions
        """
        ...
    
    async def validate_choice(
        self,
        choice: str,
        available_choices: Dict[str, Any]
    ) -> bool:
        """
        Validate if a choice is valid.
        
        Args:
            choice: User's choice
            available_choices: Available choices
            
        Returns:
            bool: True if choice is valid
        """
        ...
    
    async def get_cached_decision(
        self,
        section_number: int,
        user_response: str
    ) -> Optional[DecisionModel]:
        """
        Get cached decision if available.
        
        Args:
            section_number: Current section number
            user_response: User's response
            
        Returns:
            Optional[DecisionModel]: Cached decision if found
        """
        ...
    
    async def cache_decision(
        self,
        section_number: int,
        user_response: str,
        decision: DecisionModel
    ) -> None:
        """
        Cache a decision.
        
        Args:
            section_number: Current section number
            user_response: User's response
            decision: Decision to cache
        """
        ...
    
    def format_response(
        self,
        user_response: Optional[str],
        dice_result: Optional[int]
    ) -> str:
        """
        Format response for analysis.
        
        Args:
            user_response: User's text response
            dice_result: Result of dice roll
            
        Returns:
            str: Formatted response
        """
        ...
