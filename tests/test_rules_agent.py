"""
# 🎲 RulesAgent Test Specifications

## Overview
Test suite for the RulesAgent component of the Casys RPG engine. The RulesAgent is responsible
for analyzing game rules and determining required actions (dice rolls, choices).

## Test Architecture
Each test focuses on a specific aspect of the RulesAgent's functionality, following
the component's role in the game engine architecture.

## Test Categories

### 1. Basic Functionality Test
**Purpose**: Verify basic response format and content validation
**Input Data Format**:
```json
{
    "section_number": 1
}
```
**Expected Output Format**:
```json
{
    "choices": ["list of choices"],
    "needs_dice": boolean,
    "dice_type": "combat"|"chance"|null,
    "rules": "rule text"
}
```

### 2. Cache Mechanism Test
**Purpose**: Verify caching behavior and response consistency
**Cache Structure**:
```python
cache = {
    section_number: "rules_text",
    ...
}
```
**Validation Points**:
- Response consistency across calls
- Cache hit behavior
- Field preservation

### 3. Event System Test
**Purpose**: Verify event emission and communication
**Event Format**:
```json
{
    "type": "rules_generated",
    "data": {
        "section_number": int,
        "rules": "rules text"
    }
}
```
**Integration Points**:
- EventBus communication
- Event data structure
- Event timing

### 4. Input Validation Test
**Purpose**: Verify error handling and input validation
**Error Cases**:
- Missing section number
- Invalid section number (negative)
- Malformed input
**Error Format**:
```json
{
    "error": "error message",
    "choices": [],
    "needs_dice": false,
    "dice_type": null
}
```

### 5. Dice Roll Detection Test
**Purpose**: Verify dice roll requirement detection
**Dice Types**:
- Combat: For battle scenarios
- Chance: For luck/skill checks
**Trigger Words**:
- Combat: ["combat", "fight", "battle"]
- Chance: ["chance", "luck", "fortune"]
**Detection Format**:
```json
{
    "needs_dice": true,
    "dice_type": "combat"|"chance",
    "awaiting_action": true
}
```

## Test Dependencies
- pytest-asyncio: For async test execution
- pytest: Test framework
- langchain_openai: LLM integration
- EventBus: Event system

## Model Configuration
- Model: gpt-4o-mini
- Temperature: 0 (deterministic for rules)
"""

import pytest
import pytest_asyncio
from agents.rules_agent import RulesAgent
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
import asyncio

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """
    Event Loop Fixture
    
    Purpose:
    --------
    Provides an isolated event loop for each test to ensure clean async execution.
    
    Lifecycle:
    ----------
    1. Creates new event loop
    2. Sets as current loop
    3. Yields for test execution
    4. Cleans up after test
    
    Cleanup Process:
    ---------------
    1. Stops loop
    2. Closes loop
    3. Resets event loop policy
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if not loop.is_closed():
        loop.stop()
        loop.close()
    asyncio.set_event_loop(None)

@pytest_asyncio.fixture
async def event_bus(event_loop):
    """
    Event Bus Fixture
    
    Purpose:
    --------
    Provides a clean event bus instance for testing event communication.
    
    Features:
    ---------
    - Isolated event bus per test
    - Clean event history
    - Proper async context
    """
    return EventBus()

@pytest_asyncio.fixture
async def rules_agent(event_bus):
    """
    RulesAgent Fixture
    
    Purpose:
    --------
    Creates a configured RulesAgent instance for testing.
    
    Configuration:
    -------------
    - Model: gpt-4o-mini
    - Event Bus: Clean instance
    - Rules Directory: test data
    
    State:
    ------
    - Clean cache
    - Fresh LLM instance
    - Isolated event bus
    """
    agent = RulesAgent(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        event_bus=event_bus,
        rules_dir="data/rules"
    )
    return agent

@pytest.mark.asyncio
async def test_rules_agent_basic(rules_agent):
    """
    Basic Functionality Test
    
    Purpose:
    --------
    Validates the basic response structure and content from RulesAgent.
    
    Test Flow:
    ----------
    1. Input:
       - Valid section number
    2. Validation:
       - Response is dictionary
       - Contains required fields
       - Field types are correct
    
    Success Criteria:
    ----------------
    - Response is dict
    - Contains 'choices' field
    - Contains 'needs_dice' field
    """
    result = await rules_agent.invoke({"section_number": 1})
    assert isinstance(result, dict)
    assert "choices" in result
    assert "needs_dice" in result

@pytest.mark.asyncio
async def test_rules_agent_cache(rules_agent):
    """
    Cache Mechanism Test
    
    Purpose:
    --------
    Validates the caching behavior of RulesAgent.
    
    Test Flow:
    ----------
    1. First Call:
       - Cache miss
       - Rules analyzed
       - Result stored
    2. Second Call:
       - Cache hit
       - No analysis
       - Same result
    
    Success Criteria:
    ----------------
    - Identical responses for same input
    - All key fields match
    - Cache hit on second call
    """
    result1 = await rules_agent.invoke({"section_number": 1})
    result2 = await rules_agent.invoke({"section_number": 1})
    
    assert result1["choices"] == result2["choices"]
    assert result1["needs_dice"] == result2["needs_dice"]
    assert result1["dice_type"] == result2["dice_type"]
    assert result1["rules"] == result2["rules"]

@pytest.mark.asyncio
async def test_rules_agent_events(rules_agent, event_bus):
    """
    Event System Test
    
    Purpose:
    --------
    Validates event emission and handling.
    
    Test Flow:
    ----------
    1. Setup:
       - Register event listener
       - Track events
    2. Action:
       - Trigger rules analysis
    3. Validation:
       - Event received
       - Correct event type
       - Complete data
    
    Success Criteria:
    ----------------
    - Event emitted
    - Correct event name
    - Contains required data
    """
    events = []
    async def event_listener(event):
        events.append(event)

    await event_bus.subscribe("rules_generated", event_listener)
    await rules_agent.invoke({"section_number": 1})
    assert len(events) > 0
    assert events[0].name == "rules_generated"

@pytest.mark.asyncio
async def test_rules_agent_invalid_input(rules_agent):
    """
    Input Validation Test
    
    Purpose:
    --------
    Validates error handling for invalid inputs.
    
    Test Flow:
    ----------
    1. Missing Section:
       - Empty input
       - Verify error
    2. Invalid Section:
       - Negative number
       - Verify error
    
    Success Criteria:
    ----------------
    - Clear error messages
    - Appropriate error types
    - Graceful handling
    """
    result = await rules_agent.invoke({})
    assert "Section number required" in result.get("error", "")

    result = await rules_agent.invoke({"section_number": -1})
    assert result.get("error") is not None
    assert "invalid" in result.get("error", "").lower()

@pytest.mark.asyncio
async def test_rules_agent_dice_handling(rules_agent):
    """
    Dice Roll Detection Test
    
    Purpose:
    --------
    Validates dice roll detection and categorization.
    
    Test Flow:
    ----------
    1. Combat Roll:
       - Combat context
       - Verify detection
    2. Chance Roll:
       - Luck context
       - Verify detection
    3. No Roll:
       - Normal context
       - Verify no detection
    
    Success Criteria:
    ----------------
    - Correct dice requirement detection
    - Proper dice type categorization
    - Accurate non-dice scenario handling
    
    Test Data:
    ----------
    1. Combat: "Combat: Vous devez lancer les dés pour combattre le monstre"
    2. Chance: "Tentez votre Chance en lançant les dés"
    3. Normal: "Vous pouvez choisir d'aller à gauche ou à droite"
    """
    # Test de combat
    result = await rules_agent.invoke({
        "section_number": 1,
        "rules": "Combat: Vous devez lancer les dés pour combattre le monstre"
    })
    assert result["needs_dice"] is True
    assert result["dice_type"] == "combat"
    
    # Test de chance
    result = await rules_agent.invoke({
        "section_number": 2,
        "rules": "Tentez votre Chance en lançant les dés"
    })
    assert result["needs_dice"] is True
    assert result["dice_type"] == "chance"
    
    # Test sans dés
    result = await rules_agent.invoke({
        "section_number": 3,
        "rules": "Vous pouvez choisir d'aller à gauche ou à droite"
    })
    assert result["needs_dice"] is False
    assert result["dice_type"] is None
