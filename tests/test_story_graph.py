# tests/test_story_graph.py
from dotenv import load_dotenv
load_dotenv()

import pytest
import pytest_asyncio
from typing import Optional, Dict, Any, List, AsyncGenerator
from agents.story_graph import StoryGraph, GameState
from event_bus import EventBus, Event
import time
from unittest.mock import AsyncMock
from agents.narrator_agent import NarratorAgent
from agents.decision_agent import DecisionAgent
from agents.rules_agent import RulesAgent
from agents.trace_agent import TraceAgent

class MockEventBus:
    """Bus d'événements mocké pour les tests."""
    
    def __init__(self, initial_state=None):
        """
        Initialise le MockEventBus.
        
        Args:
            initial_state: État initial optionnel
        """
        self.state = initial_state or {}
        self.listeners = {}
        self.state_history = [self.state.copy()]  # Pour suivre l'évolution de l'état
        self.max_states = 3  # Nombre maximum d'états à conserver
        
    async def update_state(self, update: Dict):
        """Met à jour l'état et garde un historique."""
        self.state.update(update)
        self.state_history.append(self.state.copy())
        if len(self.state_history) > self.max_states:
            self.state_history.pop(0)
        await self.emit("state_updated", self.state)
        
    async def get_state(self) -> Dict:
        """Retourne l'état actuel."""
        return self.state
        
    def add_listener(self, event_type: str, callback):
        """Ajoute un écouteur d'événements."""
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(callback)
        
    async def emit(self, event_type: str, data: Dict):
        """Émet un événement."""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                await callback(Event(type=event_type, data=data))
                
    def get_state_history(self):
        """Retourne l'historique des états."""
        return self.state_history

class MockAgent:
    """Agent mocké pour les tests."""
    
    def __init__(self, result=None, event_bus=None):
        self.result = result if result is not None else {}
        self.event_bus = event_bus
        
    async def ainvoke(self, state):
        """Simule l'invocation asynchrone."""
        if isinstance(self.result, Exception):
            raise self.result
        yield {**state, **self.result}
        
    def invoke(self, state):
        """Simule l'invocation synchrone."""
        if isinstance(self.result, Exception):
            raise self.result
        return {**state, **self.result}

class MockNarratorAgent(MockAgent):
    """Simule le NarratorAgent."""
    def __init__(self, result=None, event_bus=None):
        super().__init__(result or {"content": "Test content for section 1"}, event_bus)

class MockRulesAgent(MockAgent):
    """Simule le RulesAgent."""
    def __init__(self, result=None, event_bus=None):
        super().__init__(result or {"rules": {
            "needs_dice": True,
            "dice_type": "normal",
            "conditions": [],
            "next_sections": [2],
            "rules_summary": "Test rules for section 1"
        }}, event_bus)

class MockDecisionAgent(MockAgent):
    """Simule le DecisionAgent."""
    def __init__(self, result=None, event_bus=None):
        result = result or {}
        result.setdefault("decision", {}).setdefault("awaiting_action", "choice")
        super().__init__(result, event_bus)

class MockTraceAgent(MockAgent):
    """Simule le TraceAgent."""
    def __init__(self, result=None, event_bus=None):
        super().__init__(result or {"trace": {"last_action": "choice"}}, event_bus)

class MockErrorAgent(MockAgent):
    """Agent qui simule une erreur."""
    def __init__(self, event_bus=None):
        super().__init__(Exception("Test error"), event_bus)

@pytest.fixture
def event_bus():
    """Fixture pour EventBus mocké."""
    initial_state = {
        "section_number": 1,
        "content": None,
        "rules": None,
        "decision": None,
        "error": None
    }
    return MockEventBus(initial_state)

@pytest.fixture
def mock_agents(event_bus):
    """Fixture pour créer des agents mockés."""
    narrator = MockNarratorAgent({"content": "Test content for section 1"}, event_bus)
    rules = MockRulesAgent({"rules": {
        "needs_dice": True,
        "dice_type": "normal",
        "conditions": [],
        "next_sections": [2],
        "rules_summary": "Test rules for section 1"
    }}, event_bus)
    decision = MockDecisionAgent({"decision": {"awaiting_action": "choice"}}, event_bus)
    trace = MockTraceAgent({}, event_bus)
    return narrator, rules, decision, trace

@pytest_asyncio.fixture
async def story_graph(event_bus, mock_agents):
    """Fixture pour créer un StoryGraph avec des agents mockés."""
    narrator, rules, decision, trace = mock_agents
    return StoryGraph(
        event_bus=event_bus,
        narrator_agent=narrator,
        rules_agent=rules,
        decision_agent=decision,
        trace_agent=trace
    )

@pytest.mark.asyncio
async def test_story_graph_initial_state(event_bus, mock_agents):
    """Test de l'état initial du StoryGraph."""
    narrator, rules, decision, trace = mock_agents
    story_graph = StoryGraph(
        event_bus=event_bus,
        narrator_agent=narrator,
        rules_agent=rules,
        decision_agent=decision,
        trace_agent=trace
    )
    
    initial_state = {
        "section_number": 1,
        "content": None,
        "rules": None,
        "decision": None,
        "error": None,
        "needs_content": True
    }
    
    async for state in story_graph.invoke(initial_state):
        assert state["section_number"] == 1
        assert "content" in state
        assert "rules" in state
        assert state["content"] == "Test content for section 1"
        break  # On ne teste que le premier état

@pytest.mark.asyncio
async def test_story_graph_user_response_with_dice(event_bus, mock_agents):
    """Test du StoryGraph avec une réponse utilisateur nécessitant un lancer de dés."""
    narrator, rules, decision, trace = mock_agents
    story_graph = StoryGraph(
        event_bus=event_bus,
        narrator_agent=narrator,
        rules_agent=rules,
        decision_agent=decision,
        trace_agent=trace
    )
    
    state = {
        "section_number": 1,
        "user_response": "test response",
        "dice_result": {"value": 6, "type": "normal"}
    }
    
    async for result in story_graph.invoke(state):
        assert result["section_number"] == 1
        assert result["user_response"] == "test response"
        assert result["dice_result"]["value"] == 6
        break

@pytest.mark.asyncio
async def test_story_graph_user_response_without_dice(event_bus, mock_agents):
    """Test du StoryGraph avec une réponse utilisateur sans lancer de dés."""
    narrator, rules, decision, trace = mock_agents
    story_graph = StoryGraph(
        event_bus=event_bus,
        narrator_agent=narrator,
        rules_agent=rules,
        decision_agent=decision,
        trace_agent=trace
    )
    
    state = {
        "section_number": 1,
        "user_response": "test response"
    }
    
    async for result in story_graph.invoke(state):
        assert result["section_number"] == 1
        assert result["user_response"] == "test response"
        assert "dice_result" not in result
        break

@pytest.mark.asyncio
async def test_story_graph_error_handling(event_bus):
    """Test de la gestion des erreurs dans le StoryGraph."""
    error_agent = MockErrorAgent(event_bus)
    story_graph = StoryGraph(
        event_bus=event_bus,
        narrator_agent=error_agent,
        rules_agent=error_agent,
        decision_agent=error_agent,
        trace_agent=error_agent
    )
    
    state = {
        "section_number": 1,
        "error": None,
        "needs_content": True
    }
    
    async for result in story_graph.invoke(state):
        assert "error" in result
        assert isinstance(result["error"], str)
        assert "Test error" in result["error"]
        break
