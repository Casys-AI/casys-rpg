# tests/test_story_graph.py

import pytest
import pytest_asyncio
from agents.story_graph import StoryGraph, GameState
from event_bus import EventBus, Event

class MockAgent:
    """Agent mocké de base."""
    async def astream(self, state):
        """Méthode astream à surcharger dans les classes dérivées."""
        yield {}

class MockNarratorAgent(MockAgent):
    async def astream(self, state):
        """Simule le NarratorAgent."""
        yield {"content": "Test content"}

class MockRulesAgent(MockAgent):
    async def astream(self, state):
        """Simule le RulesAgent."""
        yield {
            "needs_dice": True,
            "dice_type": "combat",
            "conditions": ["combat_required"],
            "next_sections": [2, 3],
            "rules_summary": "Combat is required."
        }

class MockDecisionAgent(MockAgent):
    async def astream(self, state):
        """Simule le DecisionAgent."""
        if state.get("dice_result"):
            yield {
                "next_section": 2,
                "awaiting_action": None,
                "analysis": "Succès du jet de dés"
            }
        elif state.get("user_response"):
            if state.get("rules", {}).get("needs_dice"):
                yield {
                    "awaiting_action": "dice_roll",
                    "dice_type": state["rules"]["dice_type"],
                    "section_number": state["section_number"],
                    "analysis": "Un jet de dés est nécessaire"
                }
            else:
                yield {
                    "next_section": 2,
                    "awaiting_action": None,
                    "analysis": "Réponse acceptée"
                }
        else:
            yield {
                "awaiting_action": "user_input",
                "section_number": state["section_number"],
                "analysis": "En attente d'une réponse"
            }

class MockTraceAgent(MockAgent):
    async def astream(self, state):
        """Simule le TraceAgent."""
        yield {
            "history": [{"action": "test"}],
            "stats": {
                "Caractéristiques": {
                    "Habileté": 12,
                    "Chance": 7
                }
            }
        }

@pytest_asyncio.fixture
async def event_bus():
    """Fixture pour EventBus."""
    return EventBus()

@pytest_asyncio.fixture
async def story_graph(event_bus):
    """Fixture pour StoryGraph avec agents mockés."""
    graph = StoryGraph(
        event_bus=event_bus,
        narrator_agent=MockNarratorAgent(),
        rules_agent=MockRulesAgent(),
        decision_agent=MockDecisionAgent(),
        trace_agent=MockTraceAgent()
    )
    return graph

@pytest.mark.asyncio
async def test_story_graph_initial_state(story_graph):
    """Test l'état initial et la demande de réponse utilisateur"""
    result = await story_graph.invoke({
        "section_number": 1,
        "needs_content": True
    })

    assert result["content"] == "Test content"
    assert result["rules"]["needs_dice"] is True
    assert result["decision"]["awaiting_action"] == "user_input"
    assert result["section_number"] == 1

@pytest.mark.asyncio
async def test_story_graph_user_response_with_dice(story_graph):
    """Test la réponse utilisateur quand un jet de dés est nécessaire"""
    # D'abord envoyer la réponse utilisateur
    result = await story_graph.invoke({
        "section_number": 1,
        "content": "Test content",
        "rules": {
            "needs_dice": True,
            "dice_type": "combat"
        },
        "user_response": "Je vais combattre"
    })

    # Vérifier qu'on attend un jet de dés
    assert result["decision"]["awaiting_action"] == "dice_roll"
    assert result["decision"]["dice_type"] == "combat"
    assert result["section_number"] == 1

    # Ensuite envoyer le résultat du dé
    result = await story_graph.invoke({
        "section_number": 1,
        "content": "Test content",
        "rules": {
            "needs_dice": True,
            "dice_type": "combat"
        },
        "dice_result": {"value": 6, "type": "combat"}
    })

    # Vérifier qu'on passe à la section suivante
    assert result["decision"]["awaiting_action"] is None
    assert result["decision"]["next_section"] == 2

@pytest.mark.asyncio
async def test_story_graph_user_response_without_dice(story_graph):
    """Test la réponse utilisateur quand aucun jet de dés n'est nécessaire"""
    # Modifier le MockRulesAgent pour ce test
    original_astream = story_graph.rules_agent.astream
    async def mock_astream(state):
        yield {
            "needs_dice": False,
            "dice_type": "normal",
            "conditions": [],
            "next_sections": [2, 3],
            "rules_summary": "No dice needed."
        }
    story_graph.rules_agent.astream = mock_astream

    result = await story_graph.invoke({
        "section_number": 1,
        "content": "Test content",
        "rules": {
            "needs_dice": False,
            "dice_type": "normal",
            "conditions": [],
            "next_sections": [2, 3],
            "rules_summary": "No dice needed."
        },
        "user_response": "Je continue mon chemin"
    })

    # Vérifier qu'on passe directement à la section suivante
    assert result["decision"]["awaiting_action"] is None
    assert result["decision"]["next_section"] == 2

@pytest.mark.asyncio
async def test_story_graph_state_reset(story_graph):
    """Test la réinitialisation de l'état lors du passage à une nouvelle section"""
    # Commencer avec un état complet
    result = await story_graph.invoke({
        "section_number": 1,
        "content": "Test content",
        "rules": {
            "needs_dice": True,
            "dice_type": "combat",
            "conditions": ["combat_required"],
            "next_sections": [2, 3],
            "rules_summary": "Combat is required."
        },
        "dice_result": {"value": 6, "type": "combat"},
        "user_response": "Je vais combattre"
    })

    # Vérifier que l'état est réinitialisé pour la nouvelle section
    assert result["section_number"] == 2
    assert result["needs_content"] is True
    assert "dice_result" not in result
    assert "user_response" not in result
    assert "rules" not in result
    assert "decision" not in result

@pytest.mark.asyncio
async def test_story_graph_event_emission(event_bus, story_graph):
    """Test l'émission d'événements"""
    events_received = []

    async def event_listener(event):
        events_received.append(event)

    await event_bus.subscribe("content_generated", event_listener)
    await event_bus.subscribe("rules_generated", event_listener)

    await story_graph.invoke({
        "section_number": 1,
        "needs_content": True
    })

    assert len(events_received) > 0
    assert any(e.type == "content_generated" for e in events_received)
    assert any(e.type == "rules_generated" for e in events_received)

@pytest.mark.asyncio
async def test_story_graph_trace_integration(story_graph):
    """Test l'intégration du TraceAgent"""
    result = await story_graph.invoke({
        "section_number": 1,
        "user_response": "Test response"
    })

    assert "history" in result
    assert "stats" in result
    assert len(result["history"]) > 0
    assert result["history"][0]["action"] == "test"

@pytest.mark.asyncio
async def test_story_graph_stats_update(story_graph):
    """Test la mise à jour des statistiques"""
    result = await story_graph.invoke({
        "section_number": 1,
        "user_response": "Test response"
    })

    assert "stats" in result
    assert result["stats"]["Caractéristiques"]["Habileté"] == 12
    assert result["stats"]["Caractéristiques"]["Chance"] == 7

@pytest.mark.asyncio
async def test_story_graph_event_emission_with_trace(event_bus, story_graph):
    """Test l'émission d'événements avec le TraceAgent"""
    events_received = []

    async def event_listener(event):
        events_received.append(event)

    await event_bus.subscribe("trace_updated", event_listener)

    await story_graph.invoke({
        "section_number": 1,
        "user_response": "Test response"
    })

    assert len(events_received) > 0
    assert any(e.type == "trace_updated" for e in events_received)
    trace_event = next(e for e in events_received if e.type == "trace_updated")
    assert "history" in trace_event.data
    assert "stats" in trace_event.data
