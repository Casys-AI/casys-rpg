"""
Tests for StoryGraph
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import AsyncMock, MagicMock, create_autospec
from agents.story_graph import StoryGraph
from models.game_state import GameState
from models.narrator_model import NarratorModel
from models.rules_model import RulesModel, DiceType
from models.decision_model import DecisionModel, DiceResult
from models.trace_model import TraceModel, TraceAction, ActionType
from agents.rules_agent import RulesAgent
from agents.decision_agent import DecisionAgent
from agents.narrator_agent import NarratorAgent
from agents.trace_agent import TraceAgent
from managers.state_manager import StateManager
from managers.trace_manager import TraceManager
from typing import Dict, Any, List, Optional, AsyncGenerator
from pydantic import Field, BaseModel
from datetime import datetime
from config.agent_config import AgentConfig

@pytest_asyncio.fixture
async def event_loop():
    """Fixture pour fournir un event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    if not loop.is_closed():
        loop.stop()
        loop.close()
    asyncio.set_event_loop(None)

@pytest.fixture
def rules_agent():
    """Fixture pour fournir un RulesAgent mocké"""
    agent = create_autospec(RulesAgent)
    agent.process_rules = AsyncMock(return_value=RulesModel(
        section_number=1,
        needs_dice=False,
        dice_type=None,
        conditions=[],
        next_sections=[2],
        choices=["Option 1", "Option 2"],
        rules_summary="Test rules",
        source="test",
        error=None,
        is_cached=False,
        last_update=datetime.now()
    ))
    return agent

@pytest.fixture
def narrator_agent():
    """Fixture pour fournir un NarratorAgent mocké"""
    agent = create_autospec(NarratorAgent)
    agent.read_section = AsyncMock(return_value={
        "content": "Test content",
        "choices": ["Option 1", "Option 2"]
    })
    return agent

@pytest.fixture
def decision_agent():
    """Fixture pour fournir un DecisionAgent mocké"""
    agent = create_autospec(DecisionAgent)
    agent.process_decision = AsyncMock(return_value={
        "awaiting_action": ActionType.USER_INPUT,
        "section_number": 1
    })
    return agent

@pytest.fixture
def trace_agent():
    """Fixture pour fournir un TraceAgent mocké"""
    agent = create_autospec(TraceAgent)
    agent.update_trace = AsyncMock(return_value={
        "stats": {},
        "history": []
    })
    return agent

@pytest.fixture
def story_graph(rules_agent, decision_agent, narrator_agent, trace_agent):
    """Fixture pour fournir un StoryGraph avec des agents mockés"""
    graph = StoryGraph(
        narrator_agent=narrator_agent,
        rules_agent=rules_agent,
        decision_agent=decision_agent,
        trace_agent=trace_agent
    )

    initial_state = GameState(
        section_number=1,
        narrative=NarratorModel(
            number=1,
            content="Test content",
            choices=["Option 1", "Option 2"],
            stats={}
        ),
        rules=RulesModel(
            section_number=1,
            needs_dice=False,
            dice_type=None,
            conditions=[],
            next_sections=[2],
            choices=["Option 1", "Option 2"],
            rules_summary="Test rules",
            source="test",
            error=None,
            is_cached=False,
            last_update=datetime.now()
        ),
        decision=DecisionModel(
            awaiting_action=ActionType.USER_INPUT,
            section_number=1
        ),
        dice_roll=DiceResult(value=None, type=DiceType.NONE),
        player_input="",
        error=None,
        debug=False,
        needs_content=True,
        stats={},
        history=[],
        trace=TraceModel()
    )

    return graph, initial_state

@pytest.mark.asyncio
async def test_story_graph_initial_state(story_graph):
    """Test l'état initial du StoryGraph."""
    graph, initial_state = story_graph
    state = initial_state
    assert state.section_number == 1
    assert state.narrative.content == "Test content"
    assert state.rules.needs_dice is False
    assert state.decision.awaiting_action == ActionType.USER_INPUT

@pytest.mark.asyncio
async def test_story_graph_user_response_with_dice(story_graph):
    """Test le traitement d'une réponse utilisateur avec dés."""
    # Configure les mocks pour simuler un lancer de dés
    graph, initial_state = story_graph
    state = GameState(
        section_number=1,
        narrative=NarratorModel(
            number=1,
            content="Test content",
            choices=["Option 1", "Option 2"],
            stats={}
        ),
        rules=RulesModel(
            section_number=1,
            needs_dice=True,
            dice_type=DiceType.NORMAL,
            conditions=[],
            next_sections=[2],
            choices=["Option 1", "Option 2"],
            rules_summary="Test rules",
            source="test",
            error=None,
            is_cached=False,
            last_update=datetime.now()
        ),
        decision=DecisionModel(
            awaiting_action=ActionType.DICE_ROLL,
            section_number=1
        ),
        dice_roll=DiceResult(value=6, type=DiceType.NORMAL),
        player_input="Option 1",
        error=None,
        debug=False,
        needs_content=True,
        stats={},
        history=[],
        trace=TraceModel()
    )

    # Simule une réponse utilisateur
    await graph.process_user_response("Option 1")

    # Vérifie que les agents ont été appelés correctement
    graph.rules_agent.process_rules.assert_called_once()
    graph.decision_agent.process_decision.assert_called_once()

@pytest.mark.asyncio
async def test_story_graph_user_response_without_dice(story_graph):
    """Test le traitement d'une réponse utilisateur sans dés."""
    # Configure les mocks pour simuler une réponse sans dés
    graph, initial_state = story_graph
    state = GameState(
        section_number=1,
        narrative=NarratorModel(
            number=1,
            content="Test content",
            choices=["Option 1", "Option 2"],
            stats={}
        ),
        rules=RulesModel(
            section_number=1,
            needs_dice=False,
            dice_type=None,
            conditions=[],
            next_sections=[2],
            choices=["Option 1", "Option 2"],
            rules_summary="Test rules",
            source="test",
            error=None,
            is_cached=False,
            last_update=datetime.now()
        ),
        decision=DecisionModel(
            awaiting_action=ActionType.USER_INPUT,
            section_number=1
        ),
        dice_roll=DiceResult(value=None, type=DiceType.NONE),
        player_input="Option 1",
        error=None,
        debug=False,
        needs_content=True,
        stats={},
        history=[],
        trace=TraceModel()
    )

    # Simule une réponse utilisateur
    await graph.process_user_response("Option 1")

    # Vérifie que les agents ont été appelés correctement
    graph.rules_agent.process_rules.assert_called_once()
    graph.decision_agent.process_decision.assert_called_once()

@pytest.mark.asyncio
async def test_story_graph_error_handling(story_graph):
    """Test la gestion des erreurs dans le StoryGraph."""
    # Configure les mocks pour simuler une erreur
    graph, initial_state = story_graph
    graph.rules_agent.process_rules.side_effect = Exception("Test error")

    # Configure l'état initial
    state = GameState(
        section_number=1,
        narrative=NarratorModel(
            number=1,
            content="Test content",
            choices=["Option 1", "Option 2"],
            stats={}
        ),
        rules=RulesModel(
            section_number=1,
            needs_dice=False,
            dice_type=None,
            conditions=[],
            next_sections=[2],
            choices=["Option 1", "Option 2"],
            rules_summary="Test rules",
            source="test",
            error=None,
            is_cached=False,
            last_update=datetime.now()
        ),
        decision=DecisionModel(
            awaiting_action=ActionType.USER_INPUT,
            section_number=1
        ),
        dice_roll=DiceResult(value=None, type=DiceType.NONE),
        player_input="",
        error=None,
        debug=False,
        needs_content=True,
        stats={},
        history=[],
        trace=TraceModel()
    )

    # Simule une réponse utilisateur qui devrait générer une erreur
    await graph.process_user_response("Option 1")

    # Vérifie que l'erreur a été gérée
    assert "Test error" in graph.state.get("error", "")
