# Game Mechanics

!!! abstract "Overview"
    Understanding the core game mechanics that power CASYS RPG's interactive storytelling system.

## Core Systems

### State Management

```mermaid
graph TD
    subgraph Game State
        GS[Game State] --> PS[Player State]
        GS --> WS[World State]
        GS --> NS[Narrative State]
    end
    
    subgraph Components
        PS --> AT[Attributes]
        PS --> IN[Inventory]
        WS --> LO[Location]
        WS --> TI[Time]
        NS --> ST[Story]
        NS --> QU[Quests]
    end
```

* **State Types**
    * Game state
    * Player state
    * World state
    * Narrative state

* **State Operations**
    * State updates
    * State validation
    * State persistence

### Decision System

```mermaid
graph LR
    subgraph Input
        PC[Player Choice]
        CS[Current State]
    end
    
    subgraph Processing
        RU[Rules]
        CO[Context]
    end
    
    subgraph Output
        NS[New State]
        CF[Consequences]
    end
    
    Input --> Processing
    Processing --> Output
```

* **Choice Generation**
    * Context analysis
    * Option generation
    * Validation

* **Consequence Handling**
    * State updates
    * Narrative impacts
    * Long-term effects

## Character System

### Attributes

* **Core Stats**
    * Strength
    * Intelligence
    * Dexterity
    * Constitution

* **Derived Stats**
    * Health
    * Energy
    * Skills
    * Abilities

### Progression

```mermaid
graph TD
    subgraph Experience
        XP[XP Gain] --> LV[Level Up]
        LV --> UP[Upgrades]
    end
    
    subgraph Improvements
        UP --> AS[Attribute Points]
        UP --> SP[Skill Points]
        UP --> AB[Abilities]
    end
```

* **Experience System**
    * XP gain
    * Level progression
    * Skill advancement

* **Character Development**
    * Attribute improvement
    * Skill learning
    * Ability unlocking

## Combat System

### Turn-Based Combat

* **Action Types**
    * Attack
    * Defend
    * Use item
    * Special ability

* **Combat Flow**
    * Initiative
    * Action selection
    * Resolution
    * Effects

### Dice System

```mermaid
graph LR
    subgraph Roll
        DI[Dice] --> MO[Modifiers]
        MO --> RE[Result]
    end
    
    subgraph Factors
        AT[Attributes]
        SK[Skills]
        CO[Context]
    end
    
    Factors --> MO
```

* **Roll Types**
    * Skill checks
    * Combat rolls
    * Saving throws

* **Modifiers**
    * Attribute bonuses
    * Skill bonuses
    * Situational modifiers

## Inventory System

### Item Management

* **Item Types**
    * Equipment
    * Consumables
    * Quest items
    * Resources

* **Operations**
    * Acquire
    * Use
    * Combine
    * Trade

### Equipment

```mermaid
graph TD
    subgraph Slots
        WE[Weapon]
        AR[Armor]
        AC[Accessory]
    end
    
    subgraph Effects
        ST[Stats]
        AB[Abilities]
        BU[Buffs]
    end
    
    Slots --> Effects
```

* **Equipment Slots**
    * Weapon
    * Armor
    * Accessories

* **Equipment Effects**
    * Stat modifications
    * Special abilities
    * Status effects

## Quest System

### Quest Management

* **Quest Types**
    * Main quests
    * Side quests
    * Dynamic events

* **Quest Components**
    * Objectives
    * Requirements
    * Rewards

### Progress Tracking

```mermaid
graph TD
    subgraph Quest
        ST[Start] --> PR[Progress]
        PR --> CO[Complete]
    end
    
    subgraph Tracking
        OB[Objectives]
        MI[Milestones]
        RE[Rewards]
    end
    
    Quest --> Tracking
```

* **Progress Types**
    * Task completion
    * Collection
    * Achievement

* **Reward Types**
    * Experience
    * Items
    * Resources
    * Story progression

## Next Steps

- Try the [Tutorial](../tutorials/index.md)
- Explore [Advanced Features](../advanced/index.md)
- Read about [Technical Implementation](../../architecture/index.md)
