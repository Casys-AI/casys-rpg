"""
Model Factory.

Cette factory est responsable de la création des modèles avec la logique métier.
Elle centralise la création des modèles pour assurer la cohérence et faciliter la maintenance.

Utilisations:
    - Création de modèles avec validation métier
    - Initialisation cohérente des modèles
    - Point central pour la logique de création des modèles
"""
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.narrator_model import NarratorModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel
from models.character_model import CharacterModel, CharacterStats

class ModelFactory:
    """Factory pour créer les modèles avec la logique métier."""
    
    @staticmethod
    def create_game_state(
        game_id: Optional[str] = None,
        session_id: Optional[str] = None,
        section_number: Optional[int] = None,
        narrative: Optional[NarratorModel] = None,
        rules: Optional[RulesModel] = None,
        decision: Optional[DecisionModel] = None,
        trace: Optional[TraceModel] = None,
        **kwargs: Dict[str, Any]
    ) -> GameState:
        """Créer un GameState vide.
        
        Cette méthode crée un GameState avec les valeurs fournies ou None.
        La génération des IDs est gérée par le StateManager.
        
        Args:
            game_id: ID du jeu (géré par StateManager)
            session_id: ID de session (géré par StateManager)
            section_number: Numéro de section
            narrative: Modèle narratif
            rules: Modèle de règles
            decision: Modèle de décision
            trace: Modèle de trace
            **kwargs: Attributs supplémentaires
            
        Returns:
            GameState: État de jeu vide
            
        Raises:
            ValueError: Si section_number < 1
        """
            
        # Création du GameState vide
        game_state = GameState(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            narrative=narrative,
            rules=rules,
            decision=decision,
            trace=trace,
            **kwargs
        )
        
        logger.debug("Created empty GameState")
        
        return game_state
    
    # Les autres méthodes create_* ne sont plus nécessaires car nous utilisons
    # directement les constructeurs des modèles existants
