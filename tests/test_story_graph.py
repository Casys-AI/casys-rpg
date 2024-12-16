# tests/test_story_graph.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from agents.story_graph import StoryGraph
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.narrator_agent import NarratorAgent
from agents.trace_agent import TraceAgent
from event_bus import EventBus, Event
import asyncio

class MockEventBus:
    """Mock pour EventBus"""
    def __init__(self):
        self.state = {}
        self.emit = AsyncMock()
        self.get_state = AsyncMock(return_value=self.state)
        self.update_state = AsyncMock()

    async def emit(self, event: Event) -> None:
        """Simule l'émission d'un événement"""
        if isinstance(event, Event):
            self.state.update(event.data)
        else:
            self.state.update(event)

    async def get_state(self) -> dict:
        """Retourne l'état actuel"""
        return self.state

    async def update_state(self, new_state: dict) -> None:
        """Met à jour l'état"""
        self.state.update(new_state)

@pytest_asyncio.fixture
async def event_bus():
    return MockEventBus()

@pytest_asyncio.fixture
async def rules_agent(event_bus):
    # Create a mock RulesAgent that doesn't need serialization
    mock_agent = MagicMock()
    async def mock_ainvoke(state):
        yield {
            "rules": {
                "needs_dice": True,
                "dice_type": "normal",
                "conditions": [],
                "next_sections": [2],
                "rules_summary": "Test rules for section 1"
            }
        }
    mock_agent.ainvoke = mock_ainvoke
    return mock_agent

@pytest_asyncio.fixture
async def narrator_agent(event_bus):
    # Create a mock NarratorAgent that doesn't need serialization
    mock_agent = MagicMock()
    async def mock_ainvoke(state):
        yield {
            "content": "Test content for section 1",
            "section_number": 1
        }
    mock_agent.ainvoke = mock_ainvoke
    return mock_agent

@pytest_asyncio.fixture
async def decision_agent(event_bus):
    # Create a mock DecisionAgent that doesn't need serialization
    mock_agent = MagicMock()
    mock_agent.invoke = AsyncMock(return_value={
        "decision": {
            "awaiting_action": "user_input",
            "section_number": 2
        }
    })
    return mock_agent

@pytest_asyncio.fixture
async def trace_agent(event_bus):
    # Create a mock TraceAgent that doesn't need serialization
    mock_agent = MagicMock()
    mock_agent.invoke = AsyncMock(return_value={
        "trace": {
            "stats": {
                "Caractéristiques": {
                    "Habileté": 10,
                    "Chance": 5,
                    "Endurance": 8
                },
                "Ressources": {
                    "Or": 100
                },
                "Inventaire": {
                    "Objets": ["Épée", "Bouclier"]
                }
            },
            "history": []
        }
    })
    return mock_agent

@pytest_asyncio.fixture
async def story_graph(event_bus, rules_agent, decision_agent, narrator_agent, trace_agent):
    return StoryGraph(
        event_bus=event_bus,
        rules_agent=rules_agent,
        decision_agent=decision_agent,
        narrator_agent=narrator_agent,
        trace_agent=trace_agent
    )

@pytest.mark.asyncio
async def test_story_graph_initial_state(story_graph):
    """Test l'état initial du StoryGraph"""
    state = None
    async for s in story_graph.invoke(state):
        state = s
        break
    
    assert state is not None
    assert state.get("section_number") == 1
    assert state.get("content") == "Test content for section 1"
    assert state.get("rules", {}).get("needs_dice") is True
    assert state.get("rules", {}).get("dice_type") == "normal"

@pytest.mark.asyncio
async def test_story_graph_user_response_with_dice(story_graph):
    """Test du StoryGraph avec une réponse utilisateur nécessitant un lancer de dés."""
    state = {
        "section_number": 1,
        "user_response": "test response",
        "dice_result": {"value": 6, "type": "normal"}
    }
    
    async for result in story_graph.invoke(state):
        assert result.get("section_number") == 1
        assert result.get("user_response") == "test response"
        assert result.get("dice_result", {}).get("value") == 6
        break

@pytest.mark.asyncio
async def test_story_graph_user_response_without_dice(story_graph):
    """Test du StoryGraph avec une réponse utilisateur sans lancer de dés."""
    state = {
        "section_number": 1,
        "user_response": "test response"
    }
    
    async for result in story_graph.invoke(state):
        assert result.get("section_number") == 1
        assert result.get("user_response") == "test response"
        assert "dice_result" not in result
        break

@pytest.mark.asyncio
async def test_story_graph_error_handling(story_graph):
    """Test de la gestion des erreurs dans le StoryGraph."""
    error_agent = MagicMock()
    
    async def mock_ainvoke(state):
        raise Exception("Test error")
        yield  # Cette ligne ne sera jamais atteinte
        
    error_agent.ainvoke = mock_ainvoke
    
    # Remplacer tous les agents par notre mock qui lève une exception
    story_graph.narrator = error_agent
    story_graph.rules = error_agent
    story_graph.decision = error_agent
    story_graph.trace = error_agent
    
    state = {
        "section_number": 1,
        "error": None,
        "needs_content": True
    }
    
    async for result in story_graph.invoke(state):
        assert isinstance(result.get("error"), str)
        assert "Test error" in result.get("error")
        break
