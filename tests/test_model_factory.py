"""
Test Model Factory.
Fournit des méthodes pour créer des modèles de test avec des valeurs par défaut.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType
from models.narrator_model import NarratorModel
from models.trace_model import TraceModel
from models.decision_model import DecisionModel
from models.character_model import CharacterModel, CharacterStats
from agents.factories.model_factory import ModelFactory

class TestModelFactory(ModelFactory):
    """Factory pour créer des modèles de test avec des valeurs par défaut."""
    
    @staticmethod
    def create_test_game_state(
        game_id: str = "test_game_id",
        session_id: str = "test_session_id",
        section_number: int = 1,
        narrative: Optional[NarratorModel] = None,
        rules: Optional[RulesModel] = None,
        decision: Optional[DecisionModel] = None,
        trace: Optional[TraceModel] = None,
        **kwargs: Dict[str, Any]
    ) -> GameState:
        """Créer un GameState pour les tests avec des valeurs par défaut.
        
        Args:
            game_id: ID du jeu pour les tests
            session_id: ID de session pour les tests
            section_number: Numéro de section pour les tests
            narrative: Modèle narratif optionnel
            rules: Modèle de règles optionnel
            decision: Modèle de décision optionnel
            trace: Modèle de trace optionnel
            **kwargs: Attributs supplémentaires
            
        Returns:
            GameState: État de jeu pour les tests
        """
        # On utilise GameState directement avec des valeurs par défaut pour les tests
        return GameState(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            narrative=narrative or TestModelFactory.create_test_narrator_model(section_number=section_number),
            rules=rules or TestModelFactory.create_test_rules_model(section_number=section_number),
            decision=decision or TestModelFactory.create_test_decision_model(section_number=section_number),
            trace=trace,
            **kwargs
        )
    
    @staticmethod
    def create_test_rules_model(
        section_number: int = 1,
        dice_type: DiceType = DiceType.NONE,
        source_type: SourceType = SourceType.RAW,
        dice_results: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any]
    ) -> RulesModel:
        """Créer un RulesModel pour les tests avec des valeurs par défaut."""
        return RulesModel(
            section_number=section_number,
            dice_type=dice_type,
            source_type=source_type,
            dice_results=dice_results or {},
            **kwargs
        )
    
    @staticmethod
    def create_test_narrator_model(
        section_number: int = 1,
        content: str = "Test narrative content",
        source_type: SourceType = SourceType.RAW,
        **kwargs: Dict[str, Any]
    ) -> NarratorModel:
        """Créer un NarratorModel pour les tests avec des valeurs par défaut."""
        return NarratorModel(
            section_number=section_number,
            content=content,
            source_type=source_type,
            **kwargs
        )
    
    @staticmethod
    def create_test_decision_model(
        section_number: int = 1,
        choices: Optional[Dict[str, Any]] = None,
        selected_choice: Optional[str] = None,
        source_type: SourceType = SourceType.RAW,
        **kwargs: Dict[str, Any]
    ) -> DecisionModel:
        """Créer un DecisionModel pour les tests avec des valeurs par défaut."""
        if choices is None:
            choices = {
                "choice1": "Test choice 1",
                "choice2": "Test choice 2"
            }
            
        return DecisionModel(
            section_number=section_number,
            choices=choices,
            selected_choice=selected_choice or "choice1",
            source_type=source_type,
            **kwargs
        )
    
    @staticmethod
    def create_test_character_model(
        endurance: int = 20,
        chance: int = 20,
        skill: int = 20,
        **kwargs: Dict[str, Any]
    ) -> CharacterModel:
        """Créer un CharacterModel pour les tests avec des valeurs par défaut."""
        return CharacterModel(
            stats=CharacterStats(
                endurance=endurance,
                chance=chance,
                skill=skill
            ),
            **kwargs
        )
