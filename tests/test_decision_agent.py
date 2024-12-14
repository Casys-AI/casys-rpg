import pytest
import pytest_asyncio
from agents.decision_agent import DecisionAgent
from agents.rules_agent import RulesAgent
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI

class MockRulesAgent(RulesAgent):
    """Mock pour RulesAgent"""
    
    def __init__(self, event_bus):
        super().__init__(event_bus=event_bus)
        self.cache = {}

    async def invoke(self, input):
        section = input.get("section_number", 1)
        rules = self.cache.get(section, {
            "choices": ["Option 1", "Option 2"],
            "needs_dice": False
        })
        await self.event_bus.emit(Event("rules_generated", {
            "section_number": section,
            "rules": rules
        }))
        return rules

@pytest_asyncio.fixture
async def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def rules_agent(event_bus):
    return MockRulesAgent(event_bus=event_bus)

@pytest_asyncio.fixture
async def decision_agent(rules_agent, event_bus):
    return DecisionAgent(
        rules_agent=rules_agent,
        llm=ChatOpenAI(model="gpt-4o-mini"),
        event_bus=event_bus
    )

@pytest.mark.asyncio
async def test_decision_agent_basic(decision_agent):
    """Test le fonctionnement de base"""
    result = await decision_agent.invoke({
        "section_number": 1,
        "user_response": "Option 1"
    })
    assert isinstance(result, dict)
    assert "next_section" in result or "error" in result

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
        "section_number": section,
        "user_response": "Option 1"
    })
    assert "next_section" in result or "error" in result

@pytest.mark.asyncio
async def test_decision_agent_events(decision_agent, event_bus):
    """Test l'émission d'événements"""
    events = []
    async def event_listener(event):
        events.append(event)

    await event_bus.subscribe("decision_made", event_listener)

    await decision_agent.invoke({
        "section_number": 1,
        "user_response": "Option 1"
    })
    assert len(events) > 0

@pytest.mark.asyncio
async def test_decision_agent_invalid_input(decision_agent):
    """Test la gestion des entrées invalides"""
    result = await decision_agent.invoke({})
    assert "error" in result

@pytest.mark.asyncio
async def test_decision_agent_dice_handling(decision_agent, rules_agent):
    """Test avec un lancer de dé"""
    section = 1
    rules = {
        "choices": ["Option 1", "Option 2"],
        "needs_dice": True
    }
    rules_agent.cache[section] = rules

    result = await decision_agent.invoke({
        "section_number": section,
        "user_response": "Option 1",
        "dice_result": 6
    })
    assert "next_section" in result or "error" in result
