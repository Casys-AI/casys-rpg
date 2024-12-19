"""State Manager
Manages game state persistence and validation.
"""

from typing import Dict, Optional, Any, List
from pydantic import BaseModel, ValidationError, ConfigDict
import json
import logging
from datetime import datetime

from config.component_config import ComponentConfig
from config.managers.state_manager_config import StateManagerConfig
from models.game_state import GameState

class StateManager(ComponentConfig[StateManagerConfig]):
    """Manages game state persistence and validation."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    config: StateManagerConfig
    current_state: Optional[GameState] = None
    state_history: List[GameState] = []
    logger: logging.Logger = logging.getLogger(__name__)

    def initialize(self) -> None:
        """Initialize state manager."""
        self.logger = logging.getLogger(__name__)
        self.current_state = None
        self.state_history = []

    async def save_state(self, state: GameState) -> bool:
        """
        Sauvegarde l'état actuel.
        
        Args:
            state: État à sauvegarder
            
        Returns:
            bool: True si la sauvegarde a réussi
        """
        try:
            # Valider l'état
            validated_state = GameState.model_validate(state)
            
            # Ajouter à l'historique
            self.state_history.append(validated_state)
            
            # Sauvegarder dans un fichier si configuré
            if self.config.save_to_file:
                state_dict = validated_state.model_dump()
                with open(self.config.state_file_path, 'w') as f:
                    json.dump(state_dict, f)
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving state: {str(e)}")
            return False

    async def load_state(self) -> Optional[GameState]:
        """
        Charge le dernier état sauvegardé.
        
        Returns:
            Optional[GameState]: État chargé ou None si erreur
        """
        try:
            if self.config.save_to_file and self.config.state_file_path.exists():
                with open(self.config.state_file_path, 'r') as f:
                    state_dict = json.load(f)
                return GameState.model_validate(state_dict)
            return None
            
        except Exception as e:
            self.logger.error(f"Error loading state: {str(e)}")
            return None

    async def update_state(self, new_state: Dict) -> bool:
        """
        Met à jour l'état actuel avec validation.
        
        Args:
            new_state: Nouvel état à appliquer
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            # Valider le nouvel état
            validated_state = GameState.model_validate(new_state)
            
            # Sauvegarder l'ancien état dans l'historique
            if self.current_state:
                self.state_history.append(self.current_state)
                
            # Mettre à jour l'état courant
            self.current_state = validated_state
            
            # Mettre à jour les stats si nécessaire
            if self.config.stats_manager and validated_state.stats:
                await self.config.stats_manager.update_stats(validated_state.stats)
                
            # Mettre en cache les règles si nécessaire
            if (self.config.cache_manager and 
                validated_state.rules and 
                validated_state.rules.source == "analysis"):
                await self.config.cache_manager.cache_rules(
                    validated_state.rules.section_number,
                    validated_state.rules
                )
                
            # Mettre à jour la trace si nécessaire
            if self.config.trace_manager and validated_state.trace:
                await self.config.trace_manager.add_trace(validated_state.trace)
                
            # Sauvegarder si configuré
            if self.config.save_to_file:
                await self.save_state(validated_state)
                
            return True
            
        except ValidationError as e:
            self.logger.error(f"State validation error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Error updating state: {str(e)}")
            return False

    async def get_cached_rules(self, section_number: int) -> Optional[Dict]:
        """
        Récupère les règles en cache pour une section.
        
        Args:
            section_number: Numéro de la section
            
        Returns:
            Optional[Dict]: Règles en cache ou None
        """
        try:
            if self.config.cache_manager:
                return await self.config.cache_manager.get_cached_rules(section_number)
            return None
        except Exception as e:
            self.logger.error(f"Error getting cached rules: {str(e)}")
            return None

    async def get_trace_history(self) -> List[Dict]:
        """
        Récupère l'historique des traces.
        
        Returns:
            List[Dict]: Liste des traces
        """
        try:
            if self.config.trace_manager:
                return await self.config.trace_manager.get_trace_history()
            return []
        except Exception as e:
            self.logger.error(f"Error getting trace history: {str(e)}")
            return []

    async def get_stats(self) -> Optional[Dict]:
        """
        Récupère les statistiques actuelles.
        
        Returns:
            Optional[Dict]: Statistiques ou None
        """
        try:
            if self.config.stats_manager:
                return await self.config.stats_manager.get_stats()
            return None
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            return None

    async def clear_cache(self) -> bool:
        """
        Vide le cache.
        
        Returns:
            bool: True si le cache a été vidé
        """
        try:
            if self.config.cache_manager:
                await self.config.cache_manager.clear_cache()
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")
            return False

    def create_error_state(self, error_message: str) -> Dict:
        """
        Crée un état d'erreur.
        
        Args:
            error_message: Message d'erreur
            
        Returns:
            Dict: État avec l'erreur
        """
        try:
            error_state = GameState.model_validate({
                "error": error_message,
                "timestamp": datetime.now().isoformat()
            })
            return error_state.model_dump()
            
        except Exception as e:
            self.logger.error(f"Error creating error state: {str(e)}")
            return GameState.model_validate({
                "error": f"Error creating error state: {str(e)}"
            }).model_dump()

    async def get_state_history(self) -> List[GameState]:
        """
        Récupère l'historique des états.
        
        Returns:
            List[GameState]: Liste des états précédents
        """
        return self.state_history.copy()
