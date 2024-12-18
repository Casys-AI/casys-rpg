"""State Manager
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, ValidationError
import json
import logging
from datetime import datetime
from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel
from models.decision_model import DecisionModel, DiceResult
from models.trace_model import TraceModel

class StateManagerConfig(BaseModel):
    """Configuration for StateManager"""
    cache_manager: Optional[Any] = None
    stats_manager: Optional[Any] = None

class StateManager(BaseModel):
    """Manages game state and persistence."""
    current_state: Optional[GameState] = None
    config: StateManagerConfig = StateManagerConfig()
    logger: logging.Logger = logging.getLogger(__name__)

    class Config:
        arbitrary_types_allowed = True

    async def get_state(self) -> Optional[Dict]:
        """Get current state."""
        try:
            if not self.current_state:
                self.current_state = GameState.create_initial_state()
                
            # Mise à jour des stats si nécessaire
            if self.config.stats_manager and not self.current_state.stats:
                self.current_state.stats = await self.config.stats_manager.get_stats()
                
            return self.current_state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error getting state: {str(e)}")
            return None

    async def update_state(self, new_state: Dict) -> bool:
        """
        Update current state.
        
        Args:
            new_state: Nouvel état à appliquer
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            # Valider et créer le nouvel état
            updated_state = GameState.model_validate(new_state)
            
            # Mettre à jour les stats si nécessaire
            if self.config.stats_manager and updated_state.stats:
                await self.config.stats_manager.update_stats(updated_state.stats)
                
            # Mettre en cache les règles si nécessaire
            if (self.config.cache_manager and 
                updated_state.rules and 
                updated_state.rules.source == "analysis"):
                await self.config.cache_manager.cache_rules(
                    updated_state.rules.section_number,
                    updated_state.rules
                )
                
            self.current_state = updated_state
            return True
            
        except ValidationError as e:
            self.logger.error(f"State validation error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating state: {str(e)}")
            return False

    def should_continue(self, state: Dict) -> bool:
        """
        Détermine si le jeu doit continuer.
        
        Args:
            state: État actuel du jeu
            
        Returns:
            bool: True si le jeu doit continuer
        """
        try:
            game_state = GameState.model_validate(state)
            
            # Stop si erreur
            if game_state.error:
                self.logger.info(f"Game stopped due to error: {game_state.error}")
                return False
                
            # Stop si fin de jeu
            if getattr(game_state, 'end_game', False):
                self.logger.info("Game ended normally")
                return False
                
            # Stop si pas de section valide
            if not game_state.section_number:
                self.logger.error("No valid section number")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error in should_continue: {str(e)}")
            return False

    def create_error_state(self, error_message: str, current_state: Optional[GameState] = None) -> Dict:
        """
        Create an error state from the current state.
        
        Args:
            error_message: Message d'erreur à ajouter
            current_state: État actuel optionnel à partir duquel créer l'état d'erreur
            
        Returns:
            Dict: État avec l'erreur
        """
        try:
            if current_state is None:
                state = GameState.create_initial_state()
            else:
                # Utiliser model_validate pour créer un nouvel état
                state = GameState.model_validate(
                    {"error": error_message},
                    update=current_state
                )
                
            return state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error creating error state: {str(e)}")
            # En cas d'erreur, créer un état initial avec l'erreur
            return GameState.model_validate(
                {"error": f"{error_message} (Error creating error state: {str(e)})"},
                update=GameState.create_initial_state()
            ).model_dump()

    async def handle_decision(self, user_response: str, state: Optional[Dict] = None) -> Dict:
        """
        Gère la décision de l'utilisateur.
        
        Args:
            user_response: Réponse de l'utilisateur
            state: État optionnel
            
        Returns:
            Dict: État mis à jour
        """
        try:
            if not state:
                state = await self.get_state()
                
            # Valider l'état actuel    
            current_state = GameState.model_validate(state)
            
            # Mettre à jour avec la réponse utilisateur
            updates = {
                "user_response": user_response,
                "decision": DecisionType.USER_INPUT
            }
            
            # Appliquer les mises à jour
            updated_state = await self.update_state(
                {**current_state.model_dump(), **updates}
            )
            
            # Mettre à jour le cache si nécessaire
            if self.config.cache_manager:
                await self.config.cache_manager.update_cache(updated_state)
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error handling decision: {str(e)}")
            return self.create_error_state(str(e), state or {})
