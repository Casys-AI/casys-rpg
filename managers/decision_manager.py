"""
Decision Manager Module
Handles decision management and validation.
"""
from typing import Dict, List, Optional
from datetime import datetime
import logging
from models.game_state import GameState
from models.decision_model import DecisionModel, AnalysisResult
from models.errors_model import DecisionError
from managers.protocols.decision_manager_protocol import DecisionManagerProtocol

class DecisionManager(DecisionManagerProtocol):
    """Manager for handling game decisions and validations."""

    def __init__(self):
        """Initialize the decision manager."""
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    async def validate_choice(
        self,
        choice: str,
        available_choices: Optional[List[str]]
    ) -> bool:
        """
        Validate if a choice is available.
        
        Args:
            choice: Choice to validate
            available_choices: List of available choices
            
        Returns:
            bool: True if valid
        """
        try:
            if not available_choices:
                return True
                
            return choice in available_choices
            
        except Exception as e:
            self.logger.error(f"Error validating choice: {e}")
            return False

    def format_response(
        self,
        response: str,
        state: GameState
    ) -> DecisionModel:
        """
        Format a response into a decision model.
        
        Args:
            response: User response to format
            state: Current game state
            
        Returns:
            DecisionModel: Formatted decision
        """
        try:
            if not state:
                raise DecisionError("Cannot format response: game state is None")
                
            return DecisionModel(
                response=response,
                timestamp=datetime.now(),
                section=state.section_number
            )
        except Exception as e:
            self.logger.error(f"Error formatting response: {e}")
            raise DecisionError(f"Failed to format response: {str(e)}")

    async def analyze_decision(
        self,
        decision: DecisionModel,
        state: GameState
    ) -> AnalysisResult:
        """
        Analyze a decision for validity and effects.
        
        Args:
            decision: Decision to analyze
            state: Current game state
            
        Returns:
            AnalysisResult: Analysis results
        """
        try:
            # Cache key for analysis
            cache_key = f"analysis_{decision.section}_{decision.response}"
            
            # Try to get from cache first
            # cached_result = await self.cache.get_cached_content(
            #     key=cache_key,
            #     namespace="decisions"
            # )
            
            # if cached_result:
            #     return AnalysisResult.model_validate(cached_result)
            
            # Perform analysis
            result = AnalysisResult(
                valid=True,  # Basic validation
                effects={},  # No effects by default
                next_section=None  # Will be determined by rules
            )
            
            # Cache the result
            # await self.cache.save_cached_content(
            #     key=cache_key,
            #     namespace="decisions",
            #     data=result.model_dump()
            # )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing decision: {e}")
            raise DecisionError(f"Failed to analyze decision: {str(e)}")
