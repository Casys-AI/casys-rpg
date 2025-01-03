# Domain Models

!!! abstract "Overview"
    Domain models represent the core business objects in CASYS RPG. Each model is built using Pydantic v2 for robust validation and serialization.

## Character Model

```mermaid
graph TD
    subgraph Character
        CH[Character] --> AT[Attributes]
        CH --> SK[Skills]
        CH --> IN[Inventory]
        CH --> ST[Status]
    end
    
    subgraph Components
        AT --> BS[Base Stats]
        SK --> AB[Abilities]
        IN --> IT[Items]
        ST --> EF[Effects]
    end
```

### Structure
```python
class CharacterModel(BaseModel):
    """Character data model."""
    
    # Basic info
    id: UUID
    name: str
    level: int
    
    # Core attributes
    attributes: AttributeSet
    skills: SkillSet
    inventory: Inventory
    status: CharacterStatus
    
    # State
    current_health: int
    max_health: int
    experience: int
    
    class Config:
        validate_assignment = True
```

## Rules Model

```mermaid
graph TD
    subgraph Rules
        RM[Rules Model] --> GM[Game Mechanics]
        RM --> CN[Constraints]
        RM --> AC[Actions]
    end
    
    subgraph Components
        GM --> ME[Mechanics]
        CN --> CO[Conditions]
        AC --> VA[Validation]
    end
```

### Structure
```python
class RulesModel(BaseModel):
    """Game rules model."""
    
    # Core rules
    mechanics: Dict[str, GameMechanic]
    constraints: List[Constraint]
    actions: Dict[str, ActionRule]
    
    # Validation
    conditions: List[Condition]
    validators: Dict[str, Validator]
    
    def validate_action(self, action: Action) -> bool:
        """Validate an action against rules."""
```

## Decision Model

```mermaid
graph TD
    subgraph Decision
        DM[Decision Model] --> CH[Choices]
        DM --> OC[Outcomes]
        DM --> CD[Conditions]
    end
    
    subgraph Analysis
        CH --> VA[Validation]
        OC --> PR[Processing]
        CD --> EV[Evaluation]
    end
```

### Structure
```python
class DecisionModel(BaseModel):
    """Decision processing model."""
    
    # Current decision
    choices: List[Choice]
    outcomes: Dict[str, Outcome]
    conditions: List[Condition]
    
    # Analysis
    context: DecisionContext
    history: List[Decision]
    
    async def analyze_choice(self, choice: str) -> AnalysisResult:
        """Analyze a player choice."""
```

## Narrator Model

```mermaid
graph TD
    subgraph Narrator
        NM[Narrator Model] --> CT[Content]
        NM --> ST[Style]
        NM --> FT[Format]
    end
    
    subgraph Generation
        CT --> GN[Generation]
        ST --> PR[Processing]
        FT --> FM[Formatting]
    end
```

### Structure
```python
class NarratorModel(BaseModel):
    """Narrative content model."""
    
    # Content
    current_scene: Scene
    dialog_history: List[Dialog]
    
    # Style
    style_settings: StyleConfig
    format_rules: FormatRules
    
    async def generate_content(self, context: Context) -> Content:
        """Generate narrative content."""
```

## Trace Model

```mermaid
graph TD
    subgraph Trace
        TM[Trace Model] --> EV[Events]
        TM --> AN[Analytics]
        TM --> DB[Debug]
    end
    
    subgraph Processing
        EV --> LG[Logging]
        AN --> PR[Processing]
        DB --> TR[Tracking]
    end
```

### Structure
```python
class TraceModel(BaseModel):
    """System tracing model."""
    
    # Event tracking
    events: List[Event]
    analytics: AnalyticsData
    debug_info: DebugInfo
    
    # Processing
    processors: Dict[str, EventProcessor]
    filters: List[EventFilter]
    
    async def log_event(self, event: Event) -> None:
        """Log a system event."""
```

## Model Validation

### Base Validation
```python
class BaseGameModel(BaseModel):
    """Base class for all game models."""
    
    @validator("*")
    def validate_fields(cls, v):
        """Base validation for all fields."""
        return v
        
    class Config:
        validate_assignment = True
        extra = "forbid"
```

### Custom Validators
```python
class CustomValidators:
    """Custom validation functions."""
    
    @staticmethod
    def validate_health(value: int) -> int:
        """Validate health values."""
        if value < 0:
            raise ValueError("Health cannot be negative")
        return value
        
    @staticmethod
    def validate_inventory(items: List[Item]) -> List[Item]:
        """Validate inventory contents."""
        return items
```

## Model Integration

### Inter-Model Communication
```python
class ModelIntegration:
    """Handle model interactions."""
    
    async def update_models(
        self,
        character: CharacterModel,
        rules: RulesModel,
        action: Action
    ) -> Tuple[CharacterModel, RulesModel]:
        """Process model updates."""
        
        # Validate action
        if await rules.validate_action(action):
            # Update character
            new_character = await character.apply_action(action)
            
            # Update rules state
            new_rules = await rules.process_action(action)
            
            return new_character, new_rules
```

## Best Practices

1. **Model Design**
    * Clear responsibilities
    * Proper validation
    * Type safety
    * Error handling

2. **Validation**
    * Field-level validation
    * Cross-field validation
    * Custom validators
    * Error messages

3. **Integration**
    * Clean interfaces
    * State consistency
    * Error propagation
    * Event handling

4. **Performance**
    * Efficient validation
    * Optimized processing
    * Memory management
    * Caching strategy
