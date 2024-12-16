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
    "state": {
        "section_number": 1
    }
}
```
**Expected Output Format**:
```json
{
    "state": {
        "choices": ["list of choices"],
        "needs_dice": boolean,
        "dice_type": "combat"|"chance"|null,
        "rules": "rule text"
    }
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
    "state": {
        "error": "error message",
        "choices": [],
        "needs_dice": false,
        "dice_type": null
    }
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
    "state": {
        "needs_dice": true,
        "dice_type": "combat"|"chance",
        "awaiting_action": true
    }
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
from agents.rules_agent import RulesAgent, RulesConfig
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel
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
    config = RulesConfig(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        rules_directory="data/rules"
    )
    agent = RulesAgent(event_bus=event_bus, config=config)
    return agent

@pytest.mark.asyncio
async def test_rules_agent_basic(rules_agent):
    """Test de base pour RulesAgent"""
    input_data = {
        "state": {
            "section_number": 1
        }
    }
    
    result = await rules_agent.invoke(input_data)
    
    # Vérification de la structure de base
    assert "state" in result
    assert "rules" in result["state"]
    assert "needs_dice" in result["state"]["rules"]
    
    # Vérification des champs attendus dans rules
    rules = result["state"]["rules"]
    assert "choices" in rules
    assert isinstance(rules["choices"], list)
    assert "dice_type" in rules
    assert "content" in rules

@pytest.mark.asyncio
async def test_rules_agent_cache(rules_agent):
    """Test la mise en cache"""
    section = 1
    first_result = None
    second_result = None
    
    async for result in rules_agent.ainvoke({"state": {"section_number": section}}):
        first_result = result
    async for result in rules_agent.ainvoke({"state": {"section_number": section}}):
        second_result = result
    
    assert first_result["state"] == second_result["state"]
    assert "source" in second_result and second_result["source"] == "cache"

@pytest.mark.asyncio
async def test_rules_agent_events(rules_agent, event_bus):
    """Test l'émission d'événements"""
    events = []
    async def event_listener(event):
        events.append(event)

    await event_bus.subscribe("rules_generated", event_listener)
    async for _ in rules_agent.ainvoke({"state": {"section_number": 1}}):
        pass
    
    assert len(events) > 0
    assert events[0].type == "rules_generated"
    assert "rules" in events[0].data

@pytest.mark.asyncio
async def test_rules_agent_invalid_input(rules_agent):
    """Test la gestion des entrées invalides"""
    async for result in rules_agent.ainvoke({"state": {}}):
        assert "error" in result["state"]
        assert result["state"].get("needs_dice") is False
        assert result["state"].get("dice_type") is None

@pytest.mark.asyncio
async def test_rules_agent_dice_handling(rules_agent):
    """Test la détection des jets de dés"""
    # Test combat
    async for result in rules_agent.ainvoke({"state": {
        "section_number": 1,
        "content": "Combat: Vous devez lancer les dés pour combattre le monstre"
    }}):
        assert result["state"]["rules"]["needs_dice"] is True
        assert result["state"]["rules"]["dice_type"] == "combat"

    # Test chance
    async for result in rules_agent.ainvoke({"state": {
        "section_number": 2,
        "content": "Tentez votre Chance en lançant les dés"
    }}):
        assert result["state"]["rules"]["needs_dice"] is True
        assert result["state"]["rules"]["dice_type"] == "chance"

    # Test sans dés
    async for result in rules_agent.ainvoke({"state": {
        "section_number": 3,
        "content": "Vous pouvez choisir d'aller à gauche ou à droite"
    }}):
        assert result["state"]["rules"]["needs_dice"] is False
        assert result["state"]["rules"]["dice_type"] is None

@pytest.mark.asyncio
async def test_rules_agent_always_analyze(rules_agent, event_bus):
    """
    Test que le RulesAgent analyse toujours les règles et émet un événement,
    même si le contenu est dans le cache.
    """
    section = 1
    events = []
    
    async def event_listener(event):
        events.append(event)
    
    await event_bus.subscribe("rules_generated", event_listener)
    
    # Premier appel - devrait analyser et mettre en cache
    first_result = None
    async for result in rules_agent.ainvoke({"state": {"section_number": section}}):
        first_result = result
    
    assert len(events) == 1
    assert events[0].type == "rules_generated"
    assert events[0].data["section_number"] == section
    assert "rules" in events[0].data
    
    # Deuxième appel - même si dans le cache, devrait quand même analyser
    events.clear()
    second_result = None
    async for result in rules_agent.ainvoke({"state": {"section_number": section}}):
        second_result = result
    
    # Vérifie que l'événement est toujours émis
    assert len(events) == 1
    assert events[0].type == "rules_generated"
    assert events[0].data["section_number"] == section
    assert "rules" in events[0].data
    
    # Vérifie que les résultats sont cohérents
    assert first_result["state"]["rules"]["needs_dice"] == second_result["state"]["rules"]["needs_dice"]
    assert first_result["state"]["rules"]["dice_type"] == second_result["state"]["rules"]["dice_type"]
    assert first_result["state"]["rules"]["content"] == second_result["state"]["rules"]["content"]
