"""Model-specific test fixtures and factories."""

import pytest
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

from models.narrator_model import NarratorModel, SourceType as NarratorSourceType
from models.game_state import GameState
from models.metadata_model import Metadata
from models.rules_model import (
    RulesModel, DiceType, SourceType as RulesSourceType,
    Choice, ChoiceType
)
from models.decision_model import DecisionModel
from models.character_model import CharacterModel, CharacterStats, Item, Inventory
from models.trace_model import TraceModel

class ModelFactory:
    """Factory for creating test models with default values."""
    
    @staticmethod
    def create_metadata(
        title: str = "Test Adventure",
        description: str = "A test narrative",
        tags: List[str] = None,
        author: str = "Test Author",
        created_at: datetime = None
    ) -> Metadata:
        """Create metadata instance."""
        return Metadata(
            title=title,
            description=description,
            tags=tags or ["test", "adventure"],
            author=author,
            created_at=created_at or datetime.now()
        )
    
    @staticmethod
    def create_narrative_content(
        raw_text: str = "Test narrative",
        formatted_text: str = "Test **narrative**",
        choices: Dict[str, str] = None
    ) -> dict:
        """Create narrative content instance."""
        return {
            "raw_text": raw_text,
            "formatted_text": formatted_text,
            "choices": choices or {"1": "Continue", "2": "Go back"}
        }
    
    @staticmethod
    def create_narrator_model(
        content: str = "Test narrative",
        metadata: Metadata = None,
        source_type: NarratorSourceType = NarratorSourceType.PROCESSED,
        section_number: int = 1
    ) -> NarratorModel:
        """Create narrator model instance."""
        return NarratorModel(
            section_number=section_number,
            content=content,
            metadata=metadata or ModelFactory.create_metadata(),
            source_type=source_type
        )
    
    @staticmethod
    def create_rule_condition(
        text: str = "Test condition",
        item_required: str = None,
        stat_check: Dict[str, Any] = None
    ) -> dict:
        """Create rule condition instance."""
        return {
            "text": text,
            "item_required": item_required,
            "stat_check": stat_check
        }
    
    @staticmethod
    def create_choice(
        text: str = "Test choice",
        type: ChoiceType = ChoiceType.DIRECT,
        dice_type: DiceType = None,
        dice_results: Dict[str, int] = None,
        conditions: List[dict] = None
    ) -> Choice:
        """Create choice instance."""
        return Choice(
            text=text,
            type=type,
            dice_type=dice_type,
            dice_results=dice_results,
            conditions=conditions or []
        )
    
    @staticmethod
    def create_rules_model(
        section_number: int = 1,
        needs_dice: bool = False,
        dice_type: DiceType = DiceType.NONE,
        conditions: List[dict] = None,
        choices: List[Choice] = None,
        source_type: RulesSourceType = RulesSourceType.PROCESSED
    ) -> RulesModel:
        """Create rules model instance."""
        return RulesModel(
            section_number=section_number,
            needs_dice=needs_dice,
            dice_type=dice_type,
            conditions=conditions or [],
            choices=choices or [],
            source_type=source_type
        )
    
    @staticmethod
    def create_choice_validation(
        valid_choices: List[str] = None,
        error_message: str = None
    ) -> dict:
        """Create choice validation instance."""
        return {
            "valid_choices": valid_choices or ["1", "2"],
            "error_message": error_message
        }
    
    @staticmethod
    def create_dice_result(
        roll: int = 6,
        success: bool = True,
        next_section: int = None
    ) -> dict:
        """Create dice result instance."""
        return {
            "roll": roll,
            "success": success,
            "next_section": next_section
        }
    
    @staticmethod
    def create_decision_model(
        section_number: int = 1,
        decision_type: str = "choice",
        choices: Dict[str, str] = None,
        validation: dict = None,
        dice_result: dict = None
    ) -> DecisionModel:
        """Create decision model instance."""
        return DecisionModel(
            section_number=section_number,
            decision_type=decision_type,
            choices=choices or {"1": "Continue", "2": "Go back"},
            validation=validation or ModelFactory.create_choice_validation(),
            dice_result=dice_result
        )
    
    @staticmethod
    def create_character_stats(
        endurance: int = 20,
        chance: int = 20,
        skill: int = 20
    ) -> CharacterStats:
        """Create character stats instance."""
        return CharacterStats(
            endurance=endurance,
            chance=chance,
            skill=skill
        )
    
    @staticmethod
    def create_item(
        name: str = "Test Item",
        quantity: int = 1,
        description: str = None
    ) -> Item:
        """Create item instance."""
        return Item(
            name=name,
            quantity=quantity,
            description=description
        )
    
    @staticmethod
    def create_inventory(
        items: Dict[str, Item] = None,
        capacity: int = 10,
        gold: int = 0
    ) -> Inventory:
        """Create inventory instance."""
        return Inventory(
            items=items or {},
            capacity=capacity,
            gold=gold
        )
    
    @staticmethod
    def create_character(
        name: str = "Test Character",
        stats: CharacterStats = None,
        inventory: Dict[str, Item] = None
    ) -> CharacterModel:
        """Create character model instance."""
        return CharacterModel(
            name=name,
            stats=stats or ModelFactory.create_character_stats(),
            inventory=ModelFactory.create_inventory(items=inventory)
        )
    
    @staticmethod
    def create_action(
        type: str = "user_input",
        description: str = "Test action",
        details: Dict[str, Any] = None,
        timestamp: datetime = None
    ) -> dict:
        """Create action instance."""
        return {
            "type": type,
            "description": description,
            "details": details or {},
            "timestamp": timestamp or datetime.now()
        }
    
    @staticmethod
    def create_trace_model(
        game_id: str = "test_game",
        session_id: str = "test_session",
        section_number: int = 1,
        actions: list[str] | None = None,
        decisions: list[str] | None = None,
        timestamp: datetime | None = None
    ) -> TraceModel:
        """Create a test trace model."""
        if actions is None:
            actions = ["Action 1", "Action 2"]
        if decisions is None:
            decisions = ["Decision 1", "Decision 2"]
        if timestamp is None:
            timestamp = datetime.now()
            
        return TraceModel(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            actions=actions,
            decisions=decisions,
            timestamp=timestamp
        )
    
    @staticmethod
    def create_game_state(
        game_id: str = "test_game",
        session_id: str = "test_session",
        section_number: int = 1,
        character: CharacterModel | None = None,
        narrative: NarratorModel | None = None,
        rules: RulesModel | None = None,
        trace: TraceModel | None = None,
        player_input: str | None = None
    ) -> GameState:
        """Create a game state instance."""
        return GameState(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            character=character,
            narrative=narrative,
            rules=rules,
            trace=trace,
            player_input=player_input
        )

    @staticmethod
    def create_test_game_state(
        game_id: str = "test_game_id",
        session_id: str = "test_session_id",
        section_number: int = 1,
        narrative: NarratorModel = None,
        rules: RulesModel = None,
        decision: DecisionModel = None,
        trace: TraceModel = None,
        character: CharacterModel = None
    ) -> GameState:
        """Create a test game state."""
        return GameState(
            game_id=game_id,
            session_id=session_id,
            section_number=section_number,
            narrative=narrative or ModelFactory.create_narrator_model(),
            rules=rules or ModelFactory.create_rules_model(),
            decision=decision or ModelFactory.create_decision_model(),
            trace=trace or ModelFactory.create_trace_model(),
            character=character or ModelFactory.create_character()
        )

    @staticmethod
    def create_test_narrator_model(
        section_number: int = 1,
        content: str = "Test narrative content"
    ) -> NarratorModel:
        """Create a test narrator model."""
        return NarratorModel(
            section_number=section_number,
            content=content
        )

@pytest.fixture
def model_factory() -> ModelFactory:
    """Provide model factory for tests."""
    return ModelFactory()

@pytest.fixture
def sample_metadata(model_factory) -> Metadata:
    """Provide sample metadata."""
    return model_factory.create_metadata()

@pytest.fixture
def sample_narrative_content(model_factory) -> dict:
    """Provide sample narrative content."""
    return model_factory.create_narrative_content()

@pytest.fixture
def sample_narrator_model(model_factory, sample_metadata) -> NarratorModel:
    """Provide sample narrator model."""
    return model_factory.create_narrator_model(
        content="Sample formatted content",
        metadata=sample_metadata,
        source_type=NarratorSourceType.PROCESSED,
        section_number=1
    )

@pytest.fixture
def sample_rule_condition(model_factory) -> dict:
    """Provide sample rule condition."""
    return model_factory.create_rule_condition()

@pytest.fixture
def sample_choice(model_factory) -> Choice:
    """Provide sample choice."""
    return model_factory.create_choice()

@pytest.fixture
def sample_rules_model(model_factory) -> RulesModel:
    """Provide sample rules model."""
    return model_factory.create_rules_model()

@pytest.fixture
def sample_choice_validation(model_factory) -> dict:
    """Provide sample choice validation."""
    return model_factory.create_choice_validation()

@pytest.fixture
def sample_dice_result(model_factory) -> dict:
    """Provide sample dice result."""
    return model_factory.create_dice_result()

@pytest.fixture
def sample_decision_model(model_factory) -> DecisionModel:
    """Provide sample decision model."""
    return model_factory.create_decision_model()

@pytest.fixture
def sample_character_stats(model_factory) -> CharacterStats:
    """Provide sample character stats."""
    return model_factory.create_character_stats()

@pytest.fixture
def sample_item(model_factory) -> Item:
    """Provide sample item."""
    return model_factory.create_item()

@pytest.fixture
def sample_inventory(model_factory) -> Inventory:
    """Provide sample inventory."""
    return model_factory.create_inventory()

@pytest.fixture
def sample_character_model(model_factory) -> CharacterModel:
    """Provide sample character model."""
    return model_factory.create_character()

@pytest.fixture
def sample_action(model_factory) -> dict:
    """Provide sample action."""
    return model_factory.create_action()

@pytest.fixture
def sample_trace_model(model_factory) -> TraceModel:
    """Provide sample trace model."""
    return model_factory.create_trace_model()

@pytest.fixture
def sample_game_state(
    model_factory,
    sample_character_model,
    sample_narrator_model,
    sample_rules_model,
    sample_decision_model,
    sample_trace_model
) -> GameState:
    """Provide sample game state."""
    return model_factory.create_game_state(
        character=sample_character_model,
        narrative=sample_narrator_model,
        rules=sample_rules_model,
        decisions=sample_decision_model,
        traces=sample_trace_model
    )
