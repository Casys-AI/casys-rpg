import pytest
import pytest_asyncio
from agents.decision_agent import DecisionAgent, DecisionConfig
from agents.rules_agent import RulesAgent
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
from langchain.chat_models.base import BaseChatModel

class MockRulesAgent:
    """Mock pour RulesAgent"""
    
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.cache = {}

    async def invoke(self, input_data):
        state = input_data.get("state", {})
        section = state.get("section_number", 1)
        rules = self.cache.get(section, {
            "choices": ["Option 1", "Option 2"],
            "needs_dice": False
        })
        await self.event_bus.emit(Event("rules_generated", {
            "section_number": section,
            "rules": rules
        }))
        return {"state": {**state, **rules}}
        
    async def ainvoke(self, input_data, config=None):
        state = input_data.get("state", {})
        section = state.get("section_number", 1)
        rules = self.cache.get(section, {
            "choices": ["Option 1", "Option 2"],
            "needs_dice": False
        })
        
        # Mettre à jour l'état
        state["rules"] = rules
        
        # Émettre l'événement
        await self.event_bus.emit(Event(
            type="rules_analyzed",
            data={
                "section_number": section,
                "rules": rules
            }
        ))
        
        # Retourner l'état mis à jour
        yield {"state": state}

@pytest_asyncio.fixture
async def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def rules_agent(event_bus):
    return MockRulesAgent(event_bus=event_bus)

@pytest_asyncio.fixture
async def decision_agent(event_bus, rules_agent):
    config = DecisionConfig(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        rules_agent=rules_agent
    )
    return DecisionAgent(
        event_bus=event_bus,
        config=config
    )

@pytest.mark.asyncio
async def test_decision_agent_basic(decision_agent):
    """Test le fonctionnement de base"""
    result = await decision_agent.invoke({
        "state": {
            "section_number": 1,
            "user_response": "Option 1"
        }
    })
    assert isinstance(result, dict)
    assert "state" in result
    state = result["state"]
    assert "next_section" in state or "error" in state

@pytest.mark.asyncio
async def test_decision_agent_with_rules(decision_agent, rules_agent):
    """Test avec des règles pré-définies"""
    section = 1
    rules = {
        "choices": ["Option 1", "Option 2"],
        "needs_dice": False
    }
    rules_agent.cache[section] = rules

    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "user_response": "Option 1",
            "rules": rules
        }
    })
    assert "state" in result
    state = result["state"]
    assert "next_section" in state or "error" in state

@pytest.mark.asyncio
async def test_decision_agent_events(decision_agent, event_bus):
    """Test l'émission d'événements"""
    events = []
    async def event_listener(event):
        events.append(event)

    # Ajouter des règles pour que _analyze_decision puisse fonctionner
    decision_agent.current_rules = {
        "choices": ["Option 1", "Option 2"],
        "next_sections": [2, 3],
        "needs_dice": False
    }

    await event_bus.subscribe("decision_made", event_listener)

    await decision_agent.invoke({
        "state": {
            "section_number": 1,
            "user_response": "Option 1"
        }
    })

    # Vérifier qu'on a reçu l'événement
    assert len(events) > 0
    assert events[0].type == "decision_made"

@pytest.mark.asyncio
async def test_decision_agent_invalid_input(decision_agent):
    """Test la gestion des entrées invalides"""
    result = await decision_agent.invoke({
        "state": {}
    })
    assert "state" in result
    assert "error" in result["state"]

@pytest.mark.asyncio
async def test_decision_agent_dice_handling(decision_agent, rules_agent):
    """Test avec un lancer de dé"""
    section = 1
    rules = {
        "choices": ["Option 1", "Option 2"],
        "needs_dice": True,
        "dice_type": "combat"
    }
    rules_agent.cache[section] = rules

    # Test sans résultat de dé
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "rules": rules
        }
    })
    assert "state" in result
    state = result["state"]
    assert state["awaiting_action"] == "dice_roll"
    assert state["dice_type"] == "combat"

    # Test avec résultat de dé
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "user_response": "Option 1",
            "dice_result": {"value": 6, "type": "combat"},
            "rules": rules
        }
    })
    assert "state" in result
    state = result["state"]
    assert "next_section" in state
    assert state["awaiting_action"] is None

@pytest.mark.asyncio
async def test_decision_agent_after_narrator(decision_agent, rules_agent, event_bus):
    """Test que l'agent attend la réponse après l'affichage d'une section"""
    section = 1
    rules = {
        "choices": ["Option 1", "Option 2"],
        "needs_dice": False
    }
    rules_agent.cache[section] = rules
    
    # Simuler l'affichage par le NarratorAgent
    event = Event(
        type="section_displayed",
        data={
            "section_number": section,
            "content": "Test content"
        }
    )
    await event_bus.emit(event)
    
    # Vérifier que l'agent attend une réponse
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "rules": rules
        }
    })
    assert "state" in result
    state = result["state"]
    assert state["awaiting_action"] == "user_response"
    assert "choices" in state
    assert state["choices"] == ["Option 1", "Option 2"]

@pytest.mark.asyncio
async def test_decision_agent_full_sequence(decision_agent, rules_agent, event_bus):
    """Test la séquence complète : affichage → réponse → dés"""
    section = 1
    rules = {
        "choices": ["Option 1", "Option 2"],
        "needs_user_response": True,
        "needs_dice": True,
        "next_action": "user_first",  # On veut d'abord la réponse, puis le dé
        "dice_type": "combat"
    }
    rules_agent.cache[section] = rules
    
    # 1. Simuler l'affichage
    event = Event(
        type="section_displayed",
        data={
            "section_number": section,
            "content": "Test content"
        }
    )
    await event_bus.emit(event)
    
    # 2. Vérifier l'attente de réponse
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "rules": rules
        }
    })
    assert result["state"]["awaiting_action"] == "user_response"
    
    # 3. Envoyer une réponse, vérifier l'attente de dés
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "user_response": "Option 1",
            "rules": rules
        }
    })
    assert result["state"]["awaiting_action"] == "dice_roll"
    assert result["state"]["dice_type"] == "combat"
    
    # 4. Envoyer le résultat des dés, vérifier la fin de séquence
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "user_response": "Option 1",
            "dice_result": {"value": 6, "type": "combat"},
            "rules": rules
        }
    })
    assert result["state"]["awaiting_action"] is None
    assert result["state"]["next_section"] == section + 1

@pytest.mark.asyncio
async def test_decision_agent_uses_rules(decision_agent, rules_agent, event_bus):
    """Test que l'agent utilise les règles pour prendre sa décision"""
    section = 1
    rules = {
        "choices": ["Aller à gauche", "Aller à droite"],
        "needs_dice": False,
        "conditions": ["Si le joueur va à gauche, il trouve un trésor"],
        "next_sections": [2, 3]
    }
    rules_agent.cache[section] = rules
    
    # 1. Simuler l'affichage
    event = Event(
        type="section_displayed",
        data={
            "section_number": section,
            "content": "Vous arrivez à une intersection. À gauche, vous voyez une lueur dorée."
        }
    )
    await event_bus.emit(event)
    
    # 2. Première invocation - devrait attendre une réponse
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "rules": rules
        }
    })
    assert result["state"]["awaiting_action"] == "user_response"
    assert result["state"]["choices"] == ["Aller à gauche", "Aller à droite"]
    
    # 3. Envoyer une réponse et vérifier la décision
    result = await decision_agent.invoke({
        "state": {
            "section_number": section,
            "user_response": "Aller à gauche",
            "rules": rules
        }
    })
    
    # La décision devrait refléter les règles
    assert result["state"]["next_section"] in rules["next_sections"]
    assert "trésor" in result["state"]["analysis"].lower()
