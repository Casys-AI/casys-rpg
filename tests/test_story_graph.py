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
    mock_agent = AsyncMock()
    async def mock_ainvoke(state):
        return {
            "state": {
                "rules": {
                    "needs_dice": True,
                    "dice_type": "normal",
                    "conditions": [],
                    "next_sections": [2],
                    "rules_summary": "Test rules for section 1"
                }
            }
        }
    mock_agent.invoke = mock_ainvoke
    return mock_agent

@pytest_asyncio.fixture
async def narrator_agent(event_bus):
    # Create a mock NarratorAgent that doesn't need serialization
    mock_agent = AsyncMock()
    async def mock_ainvoke(state):
        return {
            "state": {
                "content": "Test content for section 1",
                "section_number": 1,
                "needs_content": False
            }
        }
    mock_agent.invoke = mock_ainvoke
    return mock_agent

@pytest_asyncio.fixture
async def decision_agent(event_bus):
    # Create a mock DecisionAgent that doesn't need serialization
    mock_agent = AsyncMock()
    async def mock_ainvoke(state):
        return {
            "state": {
                "decision": {
                    "awaiting_action": "user_input",
                    "section_number": 2
                }
            }
        }
    mock_agent.invoke = mock_ainvoke
    return mock_agent

@pytest_asyncio.fixture
async def trace_agent(event_bus):
    # Create a mock TraceAgent that doesn't need serialization
    mock_agent = AsyncMock()
    async def mock_ainvoke(state):
        return {
            "state": {
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
            }
        }
    mock_agent.invoke = mock_ainvoke
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
    """Test l'état initial du StoryGraph."""
    async for result in story_graph.invoke({}):
        assert "state" in result
        state = result["state"]
        assert state.get("section_number") == 1
        assert "current_section" in state
        assert state["current_section"].get("number") == 1
        assert state.get("needs_content") is False
        assert state.get("error") is None

@pytest.mark.asyncio
async def test_story_graph_user_response_with_dice(story_graph):
    """Test le traitement d'une réponse utilisateur avec dés."""
    test_state = {
        "section_number": 1,
        "user_response": "Option 1",
        "dice_result": {"value": 6, "type": "combat"},
        "current_section": {
            "number": 1,
            "content": "Test content",
            "choices": ["Option 1", "Option 2"]
        }
    }
    
    async for result in story_graph.invoke(test_state):
        assert "state" in result
        result_state = result["state"]
        assert result_state.get("section_number") == 1
        assert result_state.get("user_response") == "Option 1"
        assert result_state.get("dice_result", {}).get("value") == 6

@pytest.mark.asyncio
async def test_story_graph_user_response_without_dice(story_graph):
    """Test le traitement d'une réponse utilisateur sans dés."""
    test_state = {
        "section_number": 1,
        "user_response": "Option 1",
        "current_section": {
            "number": 1,
            "content": "Test content",
            "choices": ["Option 1", "Option 2"]
        }
    }
    
    async for result in story_graph.invoke(test_state):
        assert "state" in result
        result_state = result["state"]
        assert result_state.get("section_number") == 1
        assert result_state.get("user_response") == "Option 1"

@pytest.mark.asyncio
async def test_story_graph_error_handling(story_graph):
    """Test la gestion des erreurs dans le StoryGraph."""
    # Créer un mock d'agent qui lève une exception
    error_agent = AsyncMock()
    error_agent.invoke = AsyncMock(side_effect=Exception("Test error"))
    
    # Remplacer tous les agents par notre mock qui lève une exception
    story_graph.narrator = error_agent
    story_graph.rules = error_agent
    story_graph.decision = error_agent
    story_graph.trace = error_agent
    
    test_state = {
        "section_number": 1,
        "current_section": {
            "number": 1,
            "content": "Test content",
            "choices": []
        },
        "needs_content": True,
        "trace": {
            "stats": {},
            "history": []
        }
    }
    
    error_found = False
    async for result in story_graph.invoke(test_state):
        if "state" in result and "error" in result["state"]:
            error = result["state"]["error"]
            assert "Test error" in error
            error_found = True
            break
    
    assert error_found, "No error was propagated"
