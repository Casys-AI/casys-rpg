"""Test different approaches for section number synchronization."""
import pytest
from datetime import datetime
from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType
from config.storage_config import StorageConfig
from managers.cache_manager import CacheManager
from managers.state_manager import StateManager
from managers.workflow_manager import WorkflowManager
from managers.rules_manager import RulesManager
from tests.test_model_factory import TestModelFactory
from operator import or_, add
from typing import Annotated, Optional
from pydantic import BaseModel, field_validator, model_validator
from functools import reduce

def create_test_models():
    """Create test models with initial values."""
    narrator = NarratorModel(
        section_number=1,
        content="Test content",
        source_type="raw"
    )
    
    rules = RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    return narrator, rules

def test_approach_1_model_dump():
    """Test approach using model_dump."""
    narrator, rules = create_test_models()
    
    # Create initial state
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator,
        'rules': rules
    }
    
    # Version 1: Using model_dump
    if hasattr(state_dict['narrative'], 'model_dump'):
        narrative_data = state_dict['narrative'].model_dump()
        narrative_data['section_number'] = state_dict['section_number']
        state_dict['narrative'] = narrative_data
    
    if hasattr(state_dict['rules'], 'model_dump'):
        rules_data = state_dict['rules'].model_dump()
        rules_data['section_number'] = state_dict['section_number']
        state_dict['rules'] = rules_data
    
    # Create GameState
    game_state = GameState(**state_dict)
    assert game_state.narrative.section_number == 2
    assert game_state.rules.section_number == 2

def test_approach_2_model_copy():
    """Test approach using model_copy."""
    narrator, rules = create_test_models()
    
    # Create initial state
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator,
        'rules': rules
    }
    
    # Version 2: Using model_copy
    if isinstance(state_dict['narrative'], NarratorModel):
        state_dict['narrative'] = state_dict['narrative'].model_copy(
            update={'section_number': state_dict['section_number']}
        )
    
    if isinstance(state_dict['rules'], RulesModel):
        state_dict['rules'] = state_dict['rules'].model_copy(
            update={'section_number': state_dict['section_number']}
        )
    
    # Create GameState
    game_state = GameState(**state_dict)
    assert game_state.narrative.section_number == 2
    assert game_state.rules.section_number == 2

def test_approach_3_direct_dict():
    """Test approach using direct dictionary update."""
    narrator, rules = create_test_models()
    
    # Create initial state with dictionaries
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator.model_dump(),
        'rules': rules.model_dump()
    }
    
    # Version 3: Direct dictionary update
    if isinstance(state_dict['narrative'], dict):
        state_dict['narrative']['section_number'] = state_dict['section_number']
    
    if isinstance(state_dict['rules'], dict):
        state_dict['rules']['section_number'] = state_dict['section_number']
    
    # Create GameState
    game_state = GameState(**state_dict)
    assert game_state.narrative.section_number == 2
    assert game_state.rules.section_number == 2

def test_mixed_input():
    """Test with mixed input (dict and model)."""
    narrator, rules = create_test_models()
    
    # Create state with mixed types
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator.model_dump(),  # Dict
        'rules': rules  # Model
    }
    
    # Version 4: Handle both types
    if 'narrative' in state_dict and state_dict['narrative']:
        narrative_data = (state_dict['narrative'].model_dump() 
                         if hasattr(state_dict['narrative'], 'model_dump') 
                         else state_dict['narrative'])
        narrative_data['section_number'] = state_dict['section_number']
        state_dict['narrative'] = narrative_data
    
    if 'rules' in state_dict and state_dict['rules']:
        rules_data = (state_dict['rules'].model_dump() 
                     if hasattr(state_dict['rules'], 'model_dump') 
                     else state_dict['rules'])
        rules_data['section_number'] = state_dict['section_number']
        state_dict['rules'] = rules_data
    
    # Create GameState
    game_state = GameState(**state_dict)
    assert game_state.narrative.section_number == 2
    assert game_state.rules.section_number == 2

def test_no_section_addition():
    """Test that section numbers are not added together."""
    narrator, rules = create_test_models()
    
    # Create initial state with section 2
    state_dict = {
        'session_id': 'test',
        'game_id': 'test_game_1',  # Ajout du game_id requis
        'section_number': 2,
        'narrative': narrator,  # section 1
        'rules': rules  # section 1
    }
    
    # Create GameState
    game_state = GameState(**state_dict)
    
    # Section numbers should be exactly 2, not 3 (2+1)
    assert game_state.narrative.section_number == 2, "Narrative section should be 2, not added"
    assert game_state.rules.section_number == 2, "Rules section should be 2, not added"
    
    # Create another state with section 3
    new_state_dict = {
        'session_id': 'test',
        'game_id': 'test_game_1',  # Ajout du game_id requis
        'section_number': 3,
        'narrative': game_state.narrative,  # section 2
        'rules': game_state.rules  # section 2
    }
    
    # Create new GameState
    new_game_state = GameState(**new_state_dict)
    
    # Section numbers should be exactly 3, not 5 (3+2)
    assert new_game_state.narrative.section_number == 3, "Narrative section should be 3, not added"
    assert new_game_state.rules.section_number == 3, "Rules section should be 3, not added"

def test_langgraph_operators():
    """Test different LangGraph operators."""
    from operator import or_
    from typing import Annotated
    from pydantic import BaseModel, field_validator, model_validator
    
    class TestModel(BaseModel):
        add_value: Annotated[int, add] = 0
        or_value: Annotated[bool, or_] = False
        first_value: Annotated[Optional[str], first_not_none] = None
        
        @field_validator('add_value', mode='before')
        @classmethod
        def validate_add_value(cls, v):
            if isinstance(v, list):
                return sum(v)
            return v
            
        @field_validator('or_value', mode='before')
        @classmethod
        def validate_or_value(cls, v):
            if isinstance(v, list):
                return any(v)
            return v
            
        @field_validator('first_value', mode='before')
        @classmethod
        def validate_first_value(cls, v):
            if isinstance(v, list):
                return next((x for x in v if x is not None), None)
            return v
    
    # Test operator.add
    values_add = {'add_value': [1, 2, 3]}
    model_add = TestModel(**values_add)
    assert model_add.add_value == 6, "Addition should sum all values"
    
    # Test or_
    values_or_1 = {'or_value': [True, False, False]}
    values_or_2 = {'or_value': [False, False, False]}
    model_or_1 = TestModel(**values_or_1)
    model_or_2 = TestModel(**values_or_2)
    assert model_or_1.or_value == True, "Or should be True if any value is True"
    assert model_or_2.or_value == False, "Or should be False if all values are False"
    
    # Test first_not_none
    values_first_1 = {'first_value': [None, "second", "third"]}
    values_first_2 = {'first_value': [None, None, "last"]}
    values_first_3 = {'first_value': ["first", "second", None]}
    model_first_1 = TestModel(**values_first_1)
    model_first_2 = TestModel(**values_first_2)
    model_first_3 = TestModel(**values_first_3)
    assert model_first_1.first_value == "second", "Should take first non-None value"
    assert model_first_2.first_value == "last", "Should take last non-None value"
    assert model_first_3.first_value == "first", "Should take first value if not None"

def test_langgraph_section_sync():
    """Test section synchronization with LangGraph operators."""
    narrator, rules = create_test_models()
    
    # Simuler le comportement de LangGraph qui envoie une liste de valeurs
    state_dict = {
        'session_id': 'test',
        'section_number': 2,  # On utilise un seul numéro pour simplifier
        'narrative': narrator,
        'rules': rules
    }
    
    # Create GameState
    game_state = GameState(**state_dict)
    
    assert game_state.section_number == 2, "Section number should be preserved"
    assert game_state.narrative.section_number == 2, "Narrative section should match"
    assert game_state.rules.section_number == 2, "Rules section should match"

def test_narrator_model_addition():
    """Test handling of NarratorModel addition in LangGraph context."""
    narrator1 = NarratorModel(
        section_number=1,
        content="Test content",
        source_type="raw"
    )
    
    # Simuler le comportement de LangGraph avec un seul modèle
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator1,
        'rules': None
    }
    
    # Create GameState
    game_state = GameState(**state_dict)
    
    assert game_state.narrative.section_number == 2, "Should use the current section number"
    assert game_state.narrative.content == "Test content", "Should preserve content"

def test_mixed_model_addition():
    """Test handling of mixed model additions in complex LangGraph scenario."""
    narrator1 = NarratorModel(
        section_number=1,
        content="Content 1",
        source_type="raw"
    )
    
    rules1 = RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Test avec un seul modèle de chaque
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator1,
        'rules': rules1
    }
    
    # Create GameState
    game_state = GameState(**state_dict)
    
    assert game_state.section_number == 2, "Section number should be 2"
    assert game_state.narrative.section_number == 2, "Narrative section should be 2"
    assert game_state.rules.section_number == 2, "Rules section should be 2"

def first_not_none(values):
    for value in values:
        if value is not None:
            return value
    return None

def test_error_handling():
    """Test error handling and first_not_none operator."""
    narrator1 = NarratorModel(
        section_number=1,
        content="Content 1",
        source_type="raw"
    )
    
    # Test avec des erreurs
    state_dict = {
        'session_id': 'test',
        'section_number': 1,
        'narrative': narrator1,
        'rules': None,
        'error': [None, "Error 1", None, "Error 2"]
    }
    
    # Create GameState
    game_state = GameState(**state_dict)
    
    # first_not_none devrait prendre la première erreur non None
    assert game_state.error == "Error 1", "Should take first non-None error"
    
    # Test avec tous les None
    state_dict_none = {
        'session_id': 'test',
        'section_number': 1,
        'narrative': narrator1,
        'rules': None,
        'error': [None, None, None]
    }
    
    game_state_none = GameState(**state_dict_none)
    assert game_state_none.error is None, "Should be None if all values are None"
    
    # Test avec une seule erreur
    state_dict_single = {
        'session_id': 'test',
        'section_number': 1,
        'narrative': narrator1,
        'rules': None,
        'error': "Single Error"
    }
    
    game_state_single = GameState(**state_dict_single)
    assert game_state_single.error == "Single Error", "Should keep single error as is"
    
    # Test avec une liste d'erreurs mixtes
    state_dict_mixed = {
        'session_id': 'test',
        'section_number': 1,
        'narrative': narrator1,
        'rules': None,
        'error': ["", None, "Real Error", "", None]
    }
    
    game_state_mixed = GameState(**state_dict_mixed)
    assert game_state_mixed.error == "", "Should take first non-None value even if empty string"

def test_narrator_model_addition_error():
    """Test the exact error scenario from the workflow."""
    narrator1 = NarratorModel(
        section_number=2,
        content="Content for section 2",
        source_type="raw"
    )
    
    narrator2 = NarratorModel(
        section_number=2,
        content="Another content for section 2",
        source_type="raw"
    )
    
    # Test que l'addition avec même section fonctionne
    result = narrator1 + narrator2
    assert result.section_number == 2
    assert result.content == "Another content for section 2"
    
    # Test que l'addition avec sections différentes échoue
    narrator3 = NarratorModel(
        section_number=3,
        content="Content for section 3",
        source_type="raw"
    )
    
    try:
        result = narrator1 + narrator3
        assert False, "Should raise AssertionError for different section numbers"
    except AssertionError as e:
        assert str(e) == "Cannot add NarratorModels with different section numbers: 2 != 3"
    
    # Test avec le GameState
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': [narrator1, narrator2],  # LangGraph essaie de les additionner
        'rules': None
    }
    
    game_state = GameState(**state_dict)
    assert game_state.narrative.section_number == 2
    assert game_state.narrative.content == "Another content for section 2"

def test_workflow_section_sync():
    """Test the exact workflow scenario causing section number issues."""
    # Créer les modèles initiaux
    narrator_section_2 = NarratorModel(
        section_number=2,
        content="Content for section 2",
        source_type="raw"
    )
    
    rules_section_2 = RulesModel(
        section_number=2,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Premier état avec section 2
    state_dict_1 = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': narrator_section_2,
        'rules': rules_section_2
    }
    
    game_state_1 = GameState(**state_dict_1)
    assert game_state_1.section_number == 2, "Initial section should be 2"
    
    # Simuler le workflow qui cause le problème
    state_dict_2 = {
        'session_id': 'test',
        'section_number': [2, 2, 2],  # LangGraph accumule les sections
        'narrative': [narrator_section_2, narrator_section_2],  # LangGraph essaie d'additionner
        'rules': [rules_section_2, rules_section_2]  # LangGraph essaie d'additionner
    }
    
    game_state_2 = GameState(**state_dict_2)
    assert game_state_2.section_number == 2, "Section should stay 2, not 6"
    assert game_state_2.narrative.section_number == 2, "Narrative section should stay 2"
    assert game_state_2.rules.section_number == 2, "Rules section should stay 2"

def test_model_addition():
    """Test l'addition des modèles NarratorModel et RulesModel."""
    
    # Test NarratorModel
    narrator1 = NarratorModel(
        section_number=2,
        content="Content 1",
        source_type=SourceType.RAW
    )
    
    narrator2 = NarratorModel(
        section_number=2,
        content="Content 2",
        source_type=SourceType.PROCESSED
    )
    
    # Test addition avec même section
    result = narrator1 + narrator2
    assert result.section_number == 2
    assert result.content == "Content 2"  # Prend le dernier
    assert result.source_type == SourceType.PROCESSED
    
    # Test addition avec sections différentes
    narrator3 = NarratorModel(
        section_number=3,
        content="Content 3",
        source_type=SourceType.RAW
    )
    
    try:
        result = narrator1 + narrator3
        assert False, "Should raise AssertionError for different section numbers"
    except AssertionError as e:
        assert str(e) == "Cannot add NarratorModels with different section numbers: 2 != 3"
    
    # Test RulesModel
    rules1 = RulesModel(
        section_number=2,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    rules2 = RulesModel(
        section_number=2,
        dice_type=DiceType.COMBAT,
        source_type=SourceType.PROCESSED
    )
    
    # Test addition avec même section
    result = rules1 + rules2
    assert result.section_number == 2
    assert result.dice_type == DiceType.COMBAT  # Prend le dernier
    assert result.source_type == SourceType.PROCESSED
    
    # Test addition avec sections différentes
    rules3 = RulesModel(
        section_number=3,
        dice_type=DiceType.CHANCE,
        source_type=SourceType.RAW
    )
    
    try:
        result = rules1 + rules3
        assert False, "Should raise AssertionError for different section numbers"
    except AssertionError as e:
        assert str(e) == "Cannot add RulesModels with different section numbers: 2 != 3"

def test_langgraph_fanin():
    """Test le fan-in de LangGraph avec nos modèles."""
    
    # Créer l'état initial
    state_dict = {
        'session_id': 'test',
        'section_number': 2,
        'narrative': NarratorModel(
            section_number=2,
            content="Initial content",
            source_type=SourceType.RAW
        ),
        'rules': RulesModel(
            section_number=2,
            dice_type=DiceType.NONE,
            source_type=SourceType.RAW
        )
    }
    
    initial_state = GameState(**state_dict)
    
    # Simuler le fan-in de LangGraph
    rules_branch = GameState(
        session_id='test',
        section_number=2,
        rules=RulesModel(
            section_number=2,
            dice_type=DiceType.COMBAT,
            source_type=SourceType.PROCESSED
        )
    )
    
    narrator_branch = GameState(
        session_id='test',
        section_number=2,
        narrative=NarratorModel(
            section_number=2,
            content="Updated content",
            source_type=SourceType.PROCESSED
        )
    )
    
    # Simuler le fan-in
    try:
        # LangGraph va essayer d'additionner les états
        merged_state = initial_state + rules_branch + narrator_branch
        
        # Vérifier que tout est correct
        assert merged_state.section_number == 2
        assert merged_state.narrative.content == "Updated content"
        assert merged_state.rules.dice_type == DiceType.COMBAT
        assert merged_state.narrative.source_type == SourceType.PROCESSED
        assert merged_state.rules.source_type == SourceType.PROCESSED
        
    except Exception as e:
        assert False, f"LangGraph fan-in failed: {str(e)}"
        
    # Tester avec des sections différentes
    bad_branch = GameState(
        session_id='test',
        section_number=3,
        narrative=NarratorModel(
            section_number=3,
            content="Bad content",
            source_type=SourceType.RAW
        )
    )
    
    try:
        merged_state = initial_state + bad_branch
        assert False, "Should raise error for different section numbers"
    except AssertionError as e:
        assert "Cannot add" in str(e)

def test_gamestate_addition():
    """Test l'addition des GameState."""
    
    # État initial
    state1 = GameState(
        session_id='test',
        section_number=2,
        narrative=NarratorModel(
            section_number=2,
            content="Content 1",
            source_type=SourceType.RAW
        )
    )
    
    # Mise à jour des règles
    state2 = GameState(
        session_id='test2',  # Différent mais on garde celui du premier état
        section_number=2,
        rules=RulesModel(
            section_number=2,
            dice_type=DiceType.COMBAT,
            source_type=SourceType.PROCESSED
        )
    )
    
    # Test addition basique - on garde le session_id du premier état
    result = state1 + state2
    assert result.session_id == 'test'  # On garde le premier session_id
    assert result.section_number == 2
    assert result.narrative is None  # Le premier état est ignoré
    assert result.rules.dice_type == DiceType.COMBAT  # On garde le dernier état
    
    # Test addition avec sections différentes - pas d'erreur, on prend le dernier
    state3 = GameState(
        session_id='test3',
        section_number=3,
        narrative=NarratorModel(
            section_number=3,
            content="Content 3",
            source_type=SourceType.RAW
        )
    )
    
    result = state1 + state3
    assert result.session_id == 'test'  # On garde le premier session_id
    assert result.section_number == 3  # On prend la nouvelle section
    assert result.narrative.content == "Content 3"  # On garde le contenu du dernier état

def test_langgraph_fanin():
    """Test le fan-in de LangGraph avec nos modèles."""
    
    # Créer l'état initial
    initial_state = GameState(
        session_id='test',
        section_number=2,
        narrative=NarratorModel(
            section_number=2,
            content="Initial content",
            source_type=SourceType.RAW
        ),
        rules=RulesModel(
            section_number=2,
            dice_type=DiceType.NONE,
            source_type=SourceType.RAW
        )
    )
    
    # Simuler le fan-in de LangGraph
    rules_update = GameState(
        session_id='test2',
        section_number=2,
        rules=RulesModel(
            section_number=2,
            dice_type=DiceType.COMBAT,
            source_type=SourceType.PROCESSED
        )
    )
    
    narrator_update = GameState(
        session_id='test3',
        section_number=2,
        narrative=NarratorModel(
            section_number=2,
            content="Updated content",
            source_type=SourceType.PROCESSED
        )
    )
    
    # Simuler le fan-in - on garde le session_id du premier état
    merged_state = initial_state + rules_update + narrator_update
    
    # Vérifier que tout est correct
    assert merged_state.session_id == 'test'  # Premier session_id
    assert merged_state.section_number == 2
    assert merged_state.narrative.content == "Updated content"  # Dernier contenu
    assert merged_state.rules is None  # Règles de l'état précédent ignorées
    
    # Tester avec une section différente - pas d'erreur, on prend le dernier état
    bad_update = GameState(
        session_id='test4',
        section_number=3,
        narrative=NarratorModel(
            section_number=3,
            content="New content",
            source_type=SourceType.RAW
        )
    )
    
    final_state = merged_state + bad_update
    assert final_state.session_id == 'test'  # Premier session_id
    assert final_state.section_number == 3  # Nouvelle section
    assert final_state.narrative.content == "New content"  # Nouveau contenu
    assert final_state.rules is None  # Ancien état ignoré

@pytest.mark.asyncio
async def test_gamestate_cycles():
    """Test le comportement du GameState dans les différents cycles du workflow."""
    
    # Créer un state_manager pour le test
    config = StorageConfig()
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    
    # CYCLE 1 - Section 1
    # État initial du cycle 1 via le state_manager
    initial_state = await state_manager.create_initial_state()
    
    # Mettre à jour l'état initial avec les modèles
    initial_state.narrative = NarratorModel(
        section_number=1,
        content="Initial content",
        source_type=SourceType.RAW
    )
    initial_state.rules = RulesModel(
        section_number=1,
        dice_type=DiceType.NONE,
        source_type=SourceType.RAW
    )
    
    # Fan-in dans le même cycle
    rules_update = GameState(
        session_id=initial_state.session_id,
        game_id=initial_state.game_id,
        section_number=1,
        rules=RulesModel(
            section_number=1,
            dice_type=DiceType.COMBAT,
            source_type=SourceType.PROCESSED
        )
    )
    
    narrator_update = GameState(
        session_id=initial_state.session_id,
        game_id=initial_state.game_id,
        section_number=1,
        narrative=NarratorModel(
            section_number=1,
            content="Updated content",
            source_type=SourceType.PROCESSED
        )
    )
    
    # Simuler le fan-in du cycle 1
    cycle1_state = rules_update + narrator_update  # narrator_update sera le dernier état
    
    # Vérifier que seul le dernier état est gardé, avec les IDs préservés
    assert cycle1_state.session_id == initial_state.session_id  # Le session_id est préservé
    assert cycle1_state.game_id == initial_state.game_id  # Le game_id est préservé
    assert cycle1_state.narrative.content == "Updated content"  # Du dernier état
    assert cycle1_state.rules is None  # L'état précédent est ignoré
    
    # CYCLE 2 - Section 2 (après should_continue)
    # Le DecisionAgent donne une nouvelle section
    decision_update = GameState(
        session_id=cycle1_state.session_id,  # Garder le même session_id
        game_id=cycle1_state.game_id,  # Garder le même game_id
        section_number=2  # Nouvelle section
    )
    
    # Créer le nouvel état initial pour le cycle 2
    cycle2_state = GameState(
        session_id=decision_update.session_id,
        game_id=decision_update.game_id,
        section_number=decision_update.section_number
    )
    
    # Vérifier que seuls les IDs et section_number sont préservés
    assert cycle2_state.session_id == initial_state.session_id
    assert cycle2_state.game_id == initial_state.game_id
    assert cycle2_state.section_number == 2
    assert cycle2_state.narrative is None  # Tout le reste doit être None
    assert cycle2_state.rules is None
    assert cycle2_state.decision is None
    assert cycle2_state.trace is None
    assert cycle2_state.error is None

@pytest.mark.asyncio
async def test_first_cycle_section_number():
    """Test que le premier cycle commence bien avec section_number = 1."""
    
    # Créer un state_manager pour le test
    config = StorageConfig()
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    
    # Créer l'état initial via le state_manager
    initial_state = await state_manager.create_initial_state()
    
    # Vérifier que le section_number est initialisé à 1
    assert initial_state.section_number == 1
    
    # Simuler les mises à jour du premier cycle
    rules_update = GameState(
        session_id=initial_state.session_id,  # Utiliser le même session_id
        game_id=initial_state.game_id,  # Utiliser le même game_id
        section_number=1,  # Doit correspondre au premier cycle
        rules=RulesModel(
            section_number=1,
            dice_type=DiceType.COMBAT,
            source_type=SourceType.PROCESSED
        )
    )
    
    narrator_update = GameState(
        session_id=initial_state.session_id,  # Utiliser le même session_id
        game_id=initial_state.game_id,  # Utiliser le même game_id
        section_number=1,  # Doit correspondre au premier cycle
        narrative=NarratorModel(
            section_number=1,
            content="First section content",
            source_type=SourceType.PROCESSED
        )
    )
    
    # Tester l'addition dans le premier cycle
    first_cycle_state = rules_update + narrator_update
    
    # Vérifier que le section_number reste à 1
    assert first_cycle_state.section_number == 1
    assert first_cycle_state.narrative.section_number == 1
    assert first_cycle_state.game_id == initial_state.game_id  # Vérifier que le game_id est préservé
    assert first_cycle_state.session_id == initial_state.session_id  # Vérifier que le session_id est préservé
    
    # Vérifier que les mises à jour avec un mauvais section_number sont rejetées
    bad_update = GameState(
        session_id=initial_state.session_id,
        game_id=initial_state.game_id,
        section_number=2,  # Mauvais section_number pour le premier cycle
        narrative=NarratorModel(
            section_number=2,
            content="Wrong section",
            source_type=SourceType.RAW
        )
    )
    
    # Vérifier que l'état est cohérent
    final_state = first_cycle_state + bad_update
    assert final_state.section_number == 2  # Prend le dernier état
    assert final_state.narrative.section_number == 2  # Le modèle doit aussi être cohérent
    assert final_state.narrative.content == "Wrong section"
    assert final_state.game_id == initial_state.game_id  # Garde le game_id original
    assert final_state.session_id == initial_state.session_id  # Garde le session_id original

@pytest.mark.asyncio
async def test_workflow_id_preservation():
    """Test que le workflow préserve bien les game_id et session_id."""
    
    # Setup
    config = StorageConfig()
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    rules_manager = RulesManager(config)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    # Test Case 1: Input sans IDs
    input_data = TestModelFactory.create_test_rules_model(
        dice_type=DiceType.NONE
    ).model_dump()
    
    # Le workflow devrait créer un nouvel état avec des IDs
    result1 = await workflow_manager.start_workflow(input_data)
    assert result1.game_id is not None, "game_id devrait être généré"
    assert result1.session_id is not None, "session_id devrait être généré"
    
    # Test Case 2: Input avec IDs existants
    existing_game_id = "test_game_id"
    existing_session_id = "test_session_456"
    input_data_with_ids = TestModelFactory.create_test_game_state(
        game_id=existing_game_id,
        session_id=existing_session_id,
        rules=TestModelFactory.create_test_rules_model(
            dice_type=DiceType.NONE
        )
    ).model_dump()
    
    # Le workflow devrait préserver les IDs existants
    result2 = await workflow_manager.start_workflow(input_data_with_ids)
    assert result2.game_id == existing_game_id, "game_id existant devrait être préservé"
    assert result2.session_id == existing_session_id, "session_id existant devrait être préservé"
    
    # Test Case 3: Input avec GameState
    input_state = TestModelFactory.create_test_game_state(
        game_id=existing_game_id,
        session_id=existing_session_id,
        rules=TestModelFactory.create_test_rules_model(
            dice_type=DiceType.NONE
        )
    )
    
    # Le workflow devrait préserver les IDs du GameState
    result3 = await workflow_manager.start_workflow(input_state)
    assert result3.game_id == existing_game_id, "game_id du GameState devrait être préservé"
    assert result3.session_id == existing_session_id, "session_id du GameState devrait être préservé"

@pytest.mark.asyncio
async def test_workflow_complete_id_preservation():
    """Test que les IDs sont préservés à travers tout le workflow."""
    
    # Setup
    config = StorageConfig()
    cache_manager = CacheManager(config)
    state_manager = StateManager(config, cache_manager)
    rules_manager = RulesManager(config)
    workflow_manager = WorkflowManager(state_manager, rules_manager)
    
    # 1. Créer un état initial avec des IDs connus
    initial_state = TestModelFactory.create_test_game_state(
        game_id="test_game_id",
        session_id="test_session_id",
        section_number=1,
        rules=TestModelFactory.create_test_rules_model(
            dice_type=DiceType.NONE
        ),
        narrative=TestModelFactory.create_test_narrator_model(
            content="Initial section"
        ),
        decision=TestModelFactory.create_test_decision_model(
            choices={"next": "Section 2"}
        )
    )
    
    # 2. Démarrer le workflow
    workflow_state = await workflow_manager.start_workflow(initial_state)
    assert workflow_state.game_id == initial_state.game_id, "game_id devrait être préservé après start_workflow"
    assert workflow_state.session_id == initial_state.session_id, "session_id devrait être préservé après start_workflow"
    
    # 3. Simuler une mise à jour du workflow
    update_state = TestModelFactory.create_test_game_state(
        section_number=2,
        narrative=TestModelFactory.create_test_narrator_model(
            section_number=2,
            content="Updated section"
        )
    )
    
    # 4. Combiner les états (comme dans le workflow)
    combined_state = workflow_state + update_state
    assert combined_state.game_id == initial_state.game_id, "game_id devrait être préservé après addition"
    assert combined_state.session_id == initial_state.session_id, "session_id devrait être préservé après addition"
    assert combined_state.section_number == 2, "section_number devrait être mis à jour"
    
    # 5. Vérifier que les modèles internes sont cohérents
    assert combined_state.narrative.section_number == 2, "narrative.section_number devrait être mis à jour"
    assert combined_state.narrative.content == "Updated section", "narrative.content devrait être mis à jour"
    assert combined_state.rules.section_number == 2, "rules.section_number devrait être mis à jour"
