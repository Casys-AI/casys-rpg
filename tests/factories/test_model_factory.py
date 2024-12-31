"""Factory pour créer des modèles de test."""
from datetime import datetime
from typing import Optional, Dict, Any

from models.game_state import GameState
from models.rules_model import RulesModel, DiceType, SourceType, Choice, ChoiceType
from models.narrator_model import NarratorModel
from models.decision_model import DecisionModel
from models.trace_model import TraceModel
from models.character_model import CharacterModel, CharacterStats, Item, Inventory
from agents.factories.model_factory import ModelFactory

class TestModelFactory(ModelFactory):
    """Factory pour créer des modèles de test avec des valeurs par défaut."""
    
    def create_game_state(
        self,
        game_id: str = "test_game_id",
        session_id: str = "test_session_id",
        section_number: int = 1,
        narrative: Optional[NarratorModel] = None,
        rules: Optional[RulesModel] = None,
        decision: Optional[DecisionModel] = None,
        trace: Optional[TraceModel] = None,
        **kwargs: Dict[str, Any]
    ) -> GameState:
        """Créer un GameState pour les tests."""
        return super().create_game_state(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            narrative=narrative or self.create_narrator_model(section_number=section_number),
            rules=rules or self.create_rules_model(section_number=section_number),
            decision=decision or self.create_decision_model(section_number=section_number),
            trace=trace,
            **kwargs
        )
    
    def create_rules_model(
        self,
        section_number: int = 1,
        dice_type: DiceType = DiceType.NONE,
        source_type: SourceType = SourceType.RAW,
        dice_results: Optional[Dict[str, Any]] = None,
        **kwargs: Dict[str, Any]
    ) -> RulesModel:
        """Créer un RulesModel pour les tests."""
        return RulesModel(
            section_number=section_number,
            dice_type=dice_type,
            source_type=source_type,
            dice_results=dice_results or {},
            **kwargs
        )
    
    def create_narrator_model(
        self,
        section_number: int = 1,
        content: str = "Test narrative content",
        source_type: SourceType = SourceType.RAW,
        **kwargs: Dict[str, Any]
    ) -> NarratorModel:
        """Créer un NarratorModel pour les tests."""
        return NarratorModel(
            section_number=section_number,
            content=content,
            source_type=source_type,
            **kwargs
        )
    
    def create_decision_model(
        self,
        section_number: int = 1,
        decision_type: ChoiceType = ChoiceType.DIRECT,
        choices: Optional[Dict[str, str]] = None,
        conditions: Optional[list[str]] = None,
        source_type: SourceType = SourceType.RAW,
        **kwargs: Dict[str, Any]
    ) -> DecisionModel:
        """Créer un DecisionModel pour les tests."""
        if choices is None:
            choices = {
                "choice1": "Test choice 1",
                "choice2": "Test choice 2"
            }
            
        return DecisionModel(
            section_number=section_number,
            type=decision_type,
            choices=choices,
            conditions=conditions or [],
            source_type=source_type,
            **kwargs
        )
    
    def create_trace_model(
        self,
        section_number: int = 1,
        game_id: str = "test_game_id",
        session_id: str = "test_session_id",
        actions: Optional[list[Dict[str, Any]]] = None,
        **kwargs: Dict[str, Any]
    ) -> TraceModel:
        """Créer un TraceModel pour les tests."""
        return TraceModel(
            section_number=section_number,
            game_id=game_id,
            session_id=session_id,
            actions=actions or [],
            **kwargs
        )
    
    def create_character(
        self,
        name: str = "Test Hero",
        stats: Optional[CharacterStats] = None,
        inventory: Optional[Inventory] = None,
        **kwargs: Dict[str, Any]
    ) -> CharacterModel:
        """Créer un CharacterModel pour les tests."""
        return CharacterModel(
            name=name,
            stats=stats or self.create_character_stats(),
            inventory=inventory or self.create_inventory(),
            **kwargs
        )
    
    def create_character_stats(
        self,
        endurance: int = 20,
        chance: int = 20,
        skill: int = 20,
        **kwargs: Dict[str, Any]
    ) -> CharacterStats:
        """Créer des CharacterStats pour les tests."""
        return CharacterStats(
            endurance=endurance,
            chance=chance,
            skill=skill,
            **kwargs
        )
    
    def create_inventory(
        self,
        capacity: int = 10,
        gold: int = 0,
        items: Optional[Dict[str, Item]] = None,
        **kwargs: Dict[str, Any]
    ) -> Inventory:
        """Créer un Inventory pour les tests."""
        return Inventory(
            capacity=capacity,
            gold=gold,
            items=items or {},
            **kwargs
        )
    
    def create_item(
        self,
        name: str = "Test Item",
        quantity: int = 1,
        description: str = "A test item",
        **kwargs: Dict[str, Any]
    ) -> Item:
        """Créer un Item pour les tests."""
        return Item(
            name=name,
            quantity=quantity,
            description=description,
            **kwargs
        )
