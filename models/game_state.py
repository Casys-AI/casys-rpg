from typing import Dict, Optional, Any, Annotated
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict, validator
import uuid
from config.logging_config import get_logger

from models.character_model import CharacterModel
from models.decision_model import DecisionModel
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType, SourceType as RulesSourceType
from models.trace_model import TraceModel
from models.errors_model import StateError

logger = get_logger('gamestate')

def first_not_none(a: Optional[str], b: Optional[str]) -> Optional[str]:
    """Return the first non-None value."""
    return a if a is not None else b

def take_last_value(a: Any, b: Any) -> Any:
    """Take the last value for LangGraph fan-in."""
    return b

def take_first_value(a: Any, b: Any) -> Any:
    """Take the first value for LangGraph fan-in."""
    return a if a is not None else b

def keep_if_not_empty(a: Any, b: Any) -> Any:
    """
    Renvoie `b` seulement si b n'est pas None et pas vide, sinon garde `a`.
    """
    if b is not None and b != "":
        return b
    return a

def take_from_node(node_name: str):
    """
    Prend la valeur seulement si elle vient du noeud spécifié.
    Sinon garde l'ancienne valeur.
    
    Args:
        node_name: Nom du noeud source ('narrator' ou 'rules')
    """
    def _take_from_node(a: Any, b: Any) -> Any:
        # Si b est une liste (cas LangGraph), prendre le dernier élément
        if isinstance(b, list):
            b = b[-1] if b else None
                
        # Vérifier la source, même si b est None
        b_node = getattr(b, '__from_node__', None) if b is not None else None
        if b_node == node_name:
            return b  # Retourner b même si c'est None
        return a
        
    return _take_from_node

def merge(a: Any, b: Any) -> Any:
    """
    Fusionne intelligemment les modèles en fonction de leur source.
    Si la valeur vient du node responsable de ce champ, on la prend toujours,
    même si elle est None (car c'est intentionnel).
    
    Pour le noeud decision, il :
    - Fusionne les données des noeuds narrator et rules
    - Garde ses propres attributs (next_section, player_input, etc.)
    - Préserve les données fusionnées des autres noeuds
    """
    # Si b est une liste (cas LangGraph), prendre le dernier élément
    if isinstance(b, list):
        b = b[-1] if b else None
    
    # Si b est None et qu'il n'y a pas de source, garder a
    if b is None and not hasattr(b, '__from_node__'):
        return a
        
    # Récupérer le nœud source
    node_name = getattr(b, '__from_node__', None)
    
    # Si c'est node_decision, prendre directement la valeur
    if node_name == 'node_decision':
        return b
        
    # Pour les autres nœuds, mettre à jour le DecisionModel existant
    if isinstance(a, DecisionModel):
        # Créer une copie du DecisionModel actuel
        updated_decision = a.model_copy()
        
        # Mettre à jour avec les données du nœud source
        if b is not None:
            model_data = b.model_dump(exclude={'section_number', 'timestamp', 'last_update', 'source_type'})
            updated_decision = updated_decision.model_copy(update=model_data)
            
        # Marquer comme venant du nœud decision
        setattr(updated_decision, '__from_node__', 'node_decision')
        return updated_decision
        
    # Pour les autres cas, garder la valeur existante
    return a

class GameStateBase(BaseModel):
    """Base state model with common fields."""
    session_id: Annotated[str, keep_if_not_empty]  # Le session_id doit être préservé
    game_id: Annotated[str, keep_if_not_empty]    # Le game_id doit être préservé
    metadata: Annotated[Optional[Dict[str, Any]], take_last_value] = None
    should_continue: Annotated[bool, take_last_value] = Field(default=False)  # False par défaut


    @field_validator('game_id')
    def validate_game_id(cls, v: str) -> str:
        """Validate that game_id is not empty."""
        if not v:
            raise StateError("game_id cannot be empty")
        return v

    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        },
        arbitrary_types_allowed=True,
        use_enum_values=True,  # Utiliser les valeurs des enums plutôt que les noms
        validate_assignment=True  # Valider lors des affectations
    )   

class GameStateInput(GameStateBase):
    """Input state for the game workflow."""
    section_number: Annotated[Optional[int], take_last_value] = Field(default=1)  # Premier cycle par défaut

    @field_validator('section_number', mode='before')
    @classmethod
    def validate_section_number(cls, v: Optional[int]) -> int:
        """Validate section number."""
        # Si None, utiliser la valeur par défaut
        if v is None:
            return 1
            
        # Valider que c'est positif
        if v < 1:
            raise StateError("Section number must be positive")
        return v

class GameStateOutput(GameStateBase):
    """Output state from the game workflow."""
    narrative: Annotated[Optional[NarratorModel], take_from_node('node_narrator')] = None
    rules: Annotated[Optional[RulesModel], take_from_node('node_rules')] = None
    decision: Annotated[Optional[DecisionModel], take_last_value] = None  # Pour gérer le fan-in
    trace: Annotated[Optional[TraceModel], merge] = None
    character: Annotated[Optional[CharacterModel], merge] = None
    
    # Error handling
    error: Annotated[Optional[str], merge] = None
    
    @field_validator('error', mode='before')
    @classmethod
    def validate_error(cls, v):
        if isinstance(v, list):
            return next((x for x in v if x is not None), None)
        return v
    
    @field_validator('narrative', 'rules', mode='before')
    @classmethod
    def validate_models(cls, v):
        if isinstance(v, list):
            # Prendre le dernier modèle de la liste
            return v[-1] if v else None
        return v

    @model_validator(mode='after')
    def sync_section_numbers(self) -> 'GameStateOutput':
        """Synchronize and validate section numbers between models."""
        if self.narrative and self.rules:
            if self.narrative.section_number != self.rules.section_number:
                raise StateError(
                    f"Section numbers must match between narrative ({self.narrative.section_number}) "
                    f"and rules ({self.rules.section_number})"
                )
        return self

class GameState(GameStateInput, GameStateOutput):
    """Complete game state at a point in time."""

    @field_validator('section_number', mode='before')
    @classmethod
    def validate_section_number(cls, v: Optional[int]) -> int:
        """Validate section number."""
        # Si None, utiliser la valeur par défaut
        if v is None:
            return 1
            
        # Valider que c'est positif
        if v < 1:
            raise StateError("Section number must be positive")
        return v

    @model_validator(mode='before')
    @classmethod
    def handle_langgraph_lists(cls, values):
        """Handle lists that may be accumulated by LangGraph."""
        # Traiter les champs qui peuvent être des listes
        fields_to_check = ['section_number', 'narrative', 'rules']
        for field in fields_to_check:
            if field in values:
                if isinstance(values[field], list):
                    if not values[field]:
                        values[field] = None
                    else:
                        values[field] = values[field][-1]  # Prendre le dernier élément
                elif isinstance(values[field], dict):
                    # Si c'est un dictionnaire, on le convertit en modèle
                    if field == 'narrative':
                        values[field] = NarratorModel(**values[field])
                    elif field == 'rules':
                        values[field] = RulesModel(**values[field])
                    
        
        # Vérifier la cohérence des sections après le traitement des listes
        narrative = values.get('narrative')
        rules = values.get('rules')
        section_number = values.get('section_number')
        
        if narrative and hasattr(narrative, 'section_number'):
            # Si pas de section_number, prendre celui du narratif
            if not section_number:
                values['section_number'] = narrative.section_number
                
        if rules and hasattr(rules, 'section_number'):
            # Si pas de section_number, prendre celui des règles
            if not section_number:
                values['section_number'] = rules.section_number
                
        # Si toujours pas de section_number, utiliser la valeur par défaut
        if not values.get('section_number'):
            values['section_number'] = 1
        
        return values

    @model_validator(mode='after')
    def validate_state(self) -> 'GameState':
        """Validate the complete state."""
        return self

    @model_validator(mode='before')
    @classmethod
    def sync_section_numbers(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize section numbers between models.
        Le section_number du GameState est la source de vérité.
        Les autres modèles doivent s'aligner sur lui.
        """
        section_number = values.get('section_number', 1)  # Default to 1 if not set
        
        # Si on a un NarratorModel, mettre à jour son section_number
        if 'narrative' in values and values['narrative']:
            if isinstance(values['narrative'], list):
                values['narrative'] = values['narrative'][-1]
            if hasattr(values['narrative'], 'section_number'):
                values['narrative'].section_number = section_number

        # Si on a un RulesModel, mettre à jour son section_number
        if 'rules' in values and values['rules']:
            if isinstance(values['rules'], list):
                values['rules'] = values['rules'][-1]
            if hasattr(values['rules'], 'section_number'):
                values['rules'].section_number = section_number

        return values

    def update_from_input(self, input_state: GameStateInput) -> None:
        """Update state from input."""
        for field in input_state.model_fields:
            if hasattr(input_state, field):
                setattr(self, field, getattr(input_state, field))
                
    def update_from_output(self, output_state: GameStateOutput) -> None:
        """Update state from output."""
        for field in output_state.model_fields:
            if hasattr(output_state, field):
                setattr(self, field, getattr(output_state, field))
                
    def to_input(self) -> GameStateInput:
        """Convert to input state."""
        return GameStateInput(
            session_id=self.session_id,
            game_id=self.game_id,
            section_number=self.section_number
        )
        
    def to_output(self) -> GameStateOutput:
        """Convert to output state."""
        return GameStateOutput(
            session_id=self.session_id,
            game_id=self.game_id,
            narrative=self.narrative,
            rules=self.rules,
            trace=self.trace,
            character=self.character,
            decision=self.decision,
            error=self.error
        )

    def with_node_updates(self, node_name: str, **updates) -> "GameState":
        """
        Create a new state with updates, marking them as coming from a specific node.
        
        Args:
            node_name: Name of the node ('node_narrator', 'node_rules', 'node_decision')
            **updates: Updates to apply to the state
            
        Returns:
            GameState: New state with marked updates
        """
        # Marquer chaque valeur avec sa source
        for value in updates.values():
            if value is not None:
                setattr(value, '__from_node__', node_name)
                
        return self.with_updates(**updates)

    def with_updates(self, **updates) -> "GameState":
        """Create a new state with updates.
        
        This method preserves both session_id and game_id when creating a new state,
        as well as the __from_node__ attribute for model instances.
        
        Args:
            **updates: Updates to apply to the state
            
        Returns:
            GameState: New state with updates applied
        """
        logger.debug("Creating new state with updates for session_id={}", self.session_id)
        logger.debug("Creating new state with updates for section_number={}", self.section_number)        
        
        # Préserver les attributs __from_node__ des modèles
        for key, value in updates.items():
            if isinstance(value, (NarratorModel, RulesModel, DecisionModel)):
                current_value = getattr(self, key, None)
                if current_value and hasattr(current_value, '__from_node__'):
                    setattr(value, '__from_node__', getattr(current_value, '__from_node__'))
        
        # Utiliser la même configuration que la property state
        state_dict = self.model_dump(
            exclude_none=False,     # Exclure les champs None comme dans state
            by_alias=True,         # Cohérence avec state
            exclude_unset=True,    # Exclure les champs non définis
            exclude={              # Exclure les champs internes spécifiques
                'session_id': False,  # Toujours inclure session_id
                'game_id': False,     # Toujours inclure game_id
                'error': False        # Toujours inclure error même si None
            }
        )
        
        # Préserver explicitement les IDs depuis l'instance
        session_id = self.session_id
        game_id = self.game_id
        
        # Appliquer les mises à jour
        state_dict.update(updates)
        
        # Toujours réinjecter les IDs
        state_dict['session_id'] = session_id
        state_dict['game_id'] = game_id
        
        return GameState(**state_dict)

    def model_dump_json(self, **kwargs):
        """Override model_dump_json to handle datetime serialization."""
        return super().model_dump_json(
            **{k: v for k, v in kwargs.items() if k != 'default'}
        )

    @classmethod
    def create_from_section(cls, section_number: int) -> 'GameState':
        """Create game state for a specific section."""
        return cls(
            section_number=section_number,
            source=RulesSourceType.RAW, 
            player_input=None,
            content=None
        )
        
    @classmethod
    def create_error_state(cls, error_message: str, session_id: str, game_id: str, section_number: int, current_state: Optional["GameState"] = None) -> "GameState":
        """Create a game state with error, optionally preserving current state."""
        if current_state:
            state_dict = current_state.model_dump()
            state_dict.update({
                "section_number": current_state.section_number,
                "error": error_message,
                "session_id": session_id,
                "game_id": game_id
            })
            return cls(**state_dict)
        
        # Pour un nouvel état, initialiser tous les champs obligatoires
        return cls(
            session_id=session_id,
            game_id=game_id,
            section_number=section_number,
            source=RulesSourceType.RAW,
            error=error_message,
            player_input=None,
            content=None,
            narrative=None,
            rules=None,
            trace=None,
            character=None,
            decision=None
        )

    @classmethod
    def create_empty_state(
        cls,
        session_id: str,
        game_id: str,
        section_number: int = 1,
    ) -> 'GameState':
        """Create a new empty state with all model fields set to None.
        
        This ensures that no old values are preserved when creating a new state.
        Use this when you want to start fresh without any previous state.
        
        Args:
            session_id: Session ID for the new state
            game_id: Game ID for the new state
            section_number: Section number (default: 1)
            
        Returns:
            GameState: New empty state
        """
        return cls(
            session_id=session_id,
            game_id=game_id,
            section_number=section_number,
            narrative=None,
            rules=None,
            decision=None,
            trace=None,
            character=None,
            error=None
        )

    @property
    def state(self) -> Dict[str, Any]: #for frontend
        """
        Get the complete state as a dictionary.
        
        Uses model_dump with configuration for proper serialization:
        - exclude_none: Remove None fields to reduce payload size
        - by_alias: Use field aliases for consistent naming
        - exclude_unset: Remove fields that weren't explicitly set
        
        Returns:
            Dict[str, Any]: Serialized state with all necessary fields
        """
        return self.model_dump(
            exclude_none=True,     # Exclure les champs None
            by_alias=True,         # Utiliser les alias pour la sérialisation
            exclude_unset=True,    # Exclure les champs non définis
            exclude={              # Exclure les champs internes spécifiques
                'session_id': False,  # Toujours inclure session_id
                'game_id': False,     # Toujours inclure game_id
                'error': False       # Toujours inclure error même si None
            }
        )
