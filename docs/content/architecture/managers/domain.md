# Domain Managers

!!! abstract "Overview"
    Domain managers handle specific aspects of the game logic, each focusing on a particular domain such as rules, decisions, narration, characters, and tracing.

## Architecture Overview

```mermaid
graph TD
    subgraph Domain Managers
        RM[Rules Manager]
        DM[Decision Manager]
        NM[Narrator Manager]
        CM[Character Manager]
        TM[Trace Manager]
    end
    
    subgraph Core Services
        AM[Agent Manager]
        SM[State Manager]
    end
    
    AM --> RM
    AM --> DM
    AM --> NM
    AM --> CM
    AM --> TM
    
    RM --> SM
    DM --> SM
    NM --> SM
    CM --> SM
    TM --> SM
```

## Rules Manager

```mermaid
graph TD
    subgraph Rules Manager
        RM[Rules Manager] --> RP[Rule Processing]
        RM --> VM[Validation Module]
        RM --> GM[Game Mechanics]
    end
    
    subgraph Components
        RP --> |Processes| RU[Rules]
        VM --> |Validates| AC[Actions]
        GM --> |Manages| ME[Mechanics]
    end
```

### Key Features
* Rule interpretation and processing
* Action validation
* Game mechanics management
* Constraint checking
* State validation

## Decision Manager

```mermaid
graph TD
    subgraph Decision Manager
        DM[Decision Manager] --> CP[Choice Processing]
        DM --> OP[Outcome Processing]
        DM --> TM[Transition Management]
    end
    
    subgraph Components
        CP --> |Processes| CH[Choices]
        OP --> |Determines| OC[Outcomes]
        TM --> |Manages| TR[Transitions]
    end
```

### Key Features
* Choice validation and processing
* Outcome determination
* State transition management
* Decision history tracking
* Context analysis

## Narrator Manager

```mermaid
graph TD
    subgraph Narrator Manager
        NM[Narrator Manager] --> CG[Content Generation]
        NM --> TF[Text Formatting]
        NM --> SM[Style Management]
    end
    
    subgraph Components
        CG --> |Generates| CO[Content]
        TF --> |Formats| TX[Text]
        SM --> |Controls| ST[Style]
    end
```

### Key Features
* Content generation and management
* Text formatting and styling
* Narrative flow control
* Response customization
* Context-aware content

## Character Manager

```mermaid
graph TD
    subgraph Character Manager
        CM[Character Manager] --> SM[State Management]
        CM --> AM[Attribute Management]
        CM --> IM[Inventory Management]
    end
    
    subgraph Components
        SM --> |Manages| ST[States]
        AM --> |Controls| AT[Attributes]
        IM --> |Handles| IN[Inventory]
    end
```

### Key Features
* Character state management
* Attribute tracking and updates
* Inventory control
* Status effects
* Character progression

## Trace Manager

```mermaid
graph TD
    subgraph Trace Manager
        TM[Trace Manager] --> EL[Event Logging]
        TM --> AN[Analytics]
        TM --> DM[Debug Module]
    end
    
    subgraph Components
        EL --> |Logs| EV[Events]
        AN --> |Analyzes| DA[Data]
        DM --> |Debugs| IS[Issues]
    end
```

### Key Features
* Event logging and tracking
* Analytics collection
* Debug information
* Performance monitoring
* History management

## Integration Patterns

### Manager Communication

```python
class DomainManager:
    async def process_event(self, event: Event) -> Result:
        # Validate with rules manager
        if await self.rules_manager.validate(event):
            # Process with specific logic
            result = await self._process(event)
            
            # Update character if needed
            await self.character_manager.update(result)
            
            # Log the event
            await self.trace_manager.log(event, result)
            
            return result
```

### State Updates

```python
class DomainManager:
    async def update_state(self, update: StateUpdate) -> None:
        # Validate update
        if await self.validate_update(update):
            # Apply update
            new_state = await self.state_manager.apply_update(update)
            
            # Notify other managers
            await self.notify_update(new_state)
            
            # Log update
            await self.trace_manager.log_update(update)
```

## Best Practices

1. **Domain Separation**
    * Clear boundaries
    * Single responsibility
    * Minimal dependencies
    * Clean interfaces

2. **State Management**
    * Atomic updates
    * Validation
    * History tracking
    * Error handling

3. **Integration**
    * Event-based communication
    * Loose coupling
    * Clear protocols
    * Error boundaries

4. **Performance**
    * Efficient processing
    * Resource management
    * Caching strategies
    * Monitoring
