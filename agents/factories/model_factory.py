"""
Model Factory.

Cette factory est responsable de la création des modèles avec la logique métier.
Elle centralise la création des modèles pour assurer la cohérence et faciliter la maintenance.

Utilisations:
    - Création de modèles avec validation métier
    - Initialisation cohérente des modèles
    - Point central pour la logique de création des modèles
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.narrator_model import NarratorModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel, ActionType, NextActionType
from models.character_model import CharacterModel

class ModelFactory:
    """Factory pour créer les modèles avec la logique métier."""
    
    @staticmethod
    def create_game_state(
        game_id: Optional[str] = None,
        session_id: Optional[str] = None,
        player_input: Optional[str] = None,
        **kwargs: Any
    ) -> GameState:
        """Créer un GameState.
        
        Args:
            game_id: ID du jeu (géré par StateManager)
            session_id: ID de session (géré par StateManager)
            player_input: Input du joueur (None par défaut)
            **kwargs: Attributs supplémentaires
            
        Returns:
            GameState: État de jeu
        """
        return GameState(
            game_id=game_id,
            session_id=session_id,
            player_input=player_input,
            **kwargs
        )
    
    @staticmethod
    def create_narrator_model(
        section_number: int,
        **kwargs: Any
    ) -> NarratorModel:
        """Create a fresh NarratorModel instance.
        
        Args:
            section_number: Current section number
            **kwargs: Additional fields to override defaults
            
        Returns:
            NarratorModel: Fresh narrator model instance
        """
        return NarratorModel(section_number=section_number, **kwargs)
    
    @staticmethod
    def create_rules_model(
        section_number: int,
        **kwargs: Any
    ) -> RulesModel:
        """Create a fresh RulesModel instance.
        
        Args:
            section_number: Current section number
            **kwargs: Additional fields to override defaults
            
        Returns:
            RulesModel: Fresh rules model instance
        """
        return RulesModel(section_number=section_number, **kwargs)
    
    @staticmethod
    def create_decision_model(
        section_number: int,
        **kwargs: Any
    ) -> DecisionModel:
        """Create a fresh DecisionModel instance.
        
        Args:
            section_number: Current section number
            **kwargs: Additional fields to override defaults
            
        Returns:
            DecisionModel: Fresh decision model instance
        """
        return DecisionModel(section_number=section_number, **kwargs)
