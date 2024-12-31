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
        section_number: int = 1,
        narrative: Optional[NarratorModel] = None,
        rules: Optional[RulesModel] = None,
        decision: Optional[DecisionModel] = None,
        trace: Optional[TraceModel] = None,
        **kwargs: Dict[str, Any]
    ) -> GameState:
        """Créer un GameState avec la logique métier.
        
        Cette méthode:
        1. Génère les IDs si non fournis
        2. Initialise tous les modèles requis avec la logique métier
        3. Valide la cohérence entre les modèles
        4. Applique les règles métier globales
        
        Args:
            game_id: ID du jeu (généré si non fourni)
            session_id: ID de session (généré si non fourni)
            section_number: Numéro de section
            narrative: Modèle narratif
            rules: Modèle de règles
            decision: Modèle de décision
            trace: Modèle de trace
            **kwargs: Attributs supplémentaires
            
        Returns:
            GameState: État de jeu initialisé avec tous les modèles requis
            
        Raises:
            ValueError: Si section_number < 1
        """
        # 1. Validation de base
        if section_number < 1:
            raise ValueError("section_number must be positive")
            
        # 2. Génération des IDs
        if not game_id:
            game_id = str(uuid.uuid4())
        if not session_id:
            session_id = str(uuid.uuid4())
            
        # 3. Initialisation des modèles avec la logique métier
        rules_model = rules or RulesModel(
            section_number=section_number,
            dice_type=DiceType.NONE,
            source_type=SourceType.RAW,
            dice_results={}
        )
        
        narrator_model = narrative or NarratorModel(
            section_number=section_number,
            content=f"Section {section_number}",
            source_type=SourceType.RAW
        )
        
        decision_model = decision or DecisionModel(
            section_number=section_number,
            choices={},
            source_type=SourceType.RAW
        )
        
        # TODO: ajouter la construction de trace
        trace_model = trace
            
        # 4. Validation de la cohérence entre les modèles
        if rules_model.section_number != section_number:
            raise ValueError(f"rules_model.section_number ({rules_model.section_number}) != section_number ({section_number})")
        if narrator_model.section_number != section_number:
            raise ValueError(f"narrator_model.section_number ({narrator_model.section_number}) != section_number ({section_number})")
        if decision_model.section_number != section_number:
            raise ValueError(f"decision_model.section_number ({decision_model.section_number}) != section_number ({section_number})")
            
        # 5. Création du GameState avec tous les modèles initialisés
        return GameState(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            narrative=narrator_model,
            rules=rules_model,
            decision=decision_model,
            trace=trace_model,
            **kwargs
        )
    
    # Les autres méthodes create_* ne sont plus nécessaires car nous utilisons
    # directement les constructeurs des modèles existants
