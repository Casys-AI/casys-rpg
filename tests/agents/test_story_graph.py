"""Tests for the story graph module."""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any

from agents import StoryGraph
from agents.factories.game_factory import GameFactory
from agents.factories.model_factory import ModelFactory
from agents.protocols import (
    StoryGraphProtocol, NarratorAgentProtocol, RulesAgentProtocol,
    DecisionAgentProtocol, TraceAgentProtocol
)
from managers.protocols import WorkflowManagerProtocol, StateManagerProtocol

from models import (
    GameState, CharacterModel, CharacterStats,
    NarratorModel, RulesModel, DiceType, Choice, ChoiceType,
    DecisionModel, TraceModel, StoryGraphError
)
from config.agents.agent_config_base import AgentConfigBase

@pytest.fixture
def mock_workflow_manager() -> WorkflowManagerProtocol:
    """Create a mock workflow manager."""
    manager = AsyncMock(spec=WorkflowManagerProtocol)
    manager.process_workflow = AsyncMock()
    manager.validate_workflow = AsyncMock(return_value=True)
    return manager

@pytest.fixture
def mock_state_manager() -> StateManagerProtocol:
    """Create a mock state manager."""
    manager = AsyncMock(spec=StateManagerProtocol)
    manager.get_state = AsyncMock()
    manager.save_state = AsyncMock()
    return manager

@pytest.fixture
def mock_narrator_agent() -> NarratorAgentProtocol:
    """Create a mock narrator agent."""
    agent = AsyncMock(spec=NarratorAgentProtocol)
    agent.process_narrative = AsyncMock()
    return agent

@pytest.fixture
def mock_rules_agent() -> RulesAgentProtocol:
    """Create a mock rules agent."""
    agent = AsyncMock(spec=RulesAgentProtocol)
    agent.process_rules = AsyncMock()
    return agent

@pytest.fixture
def mock_decision_agent() -> DecisionAgentProtocol:
    """Create a mock decision agent."""
    agent = AsyncMock(spec=DecisionAgentProtocol)
    agent.process_decision = AsyncMock()
    return agent

@pytest.fixture
def mock_trace_agent() -> TraceAgentProtocol:
    """Create a mock trace agent."""
    agent = AsyncMock(spec=TraceAgentProtocol)
    agent.process_trace = AsyncMock()
    return agent

@pytest.fixture
def model_factory() -> ModelFactory:
    """Create a model factory for testing."""
    return ModelFactory()

@pytest.fixture
def game_factory(
    mock_workflow_manager, mock_state_manager,
    mock_narrator_agent, mock_rules_agent,
    mock_decision_agent, mock_trace_agent
) -> GameFactory:
    """Create a game factory for testing."""
    return GameFactory(
        workflow_manager=mock_workflow_manager,
        state_manager=mock_state_manager,
        narrator_agent=mock_narrator_agent,
        rules_agent=mock_rules_agent,
        decision_agent=mock_decision_agent,
        trace_agent=mock_trace_agent
    )

@pytest.fixture
def story_graph_config() -> AgentConfigBase:
    """Create a test story graph config."""
    config = AgentConfigBase()
    config.llm = AsyncMock()
    config.system_message = "Test system message"
    return config

@pytest_asyncio.fixture
async def story_graph(
    story_graph_config, mock_workflow_manager,
    mock_narrator_agent, mock_rules_agent,
    mock_decision_agent, mock_trace_agent
) -> StoryGraphProtocol:
    """Create a test story graph."""
    return StoryGraph(
        config=story_graph_config,
        workflow_manager=mock_workflow_manager,
        narrator_agent=mock_narrator_agent,
        rules_agent=mock_rules_agent,
        decision_agent=mock_decision_agent,
        trace_agent=mock_trace_agent
    )

@pytest.fixture
def sample_character(model_factory) -> CharacterModel:
    """Create a sample character for testing."""
    return model_factory.create_character(
        name="Test Character",
        stats=CharacterStats(SKILL=10, STAMINA=20, LUCK=5),
        inventory=["sword", "potion"]
    )

@pytest.fixture
def sample_metadata() -> Dict[str, Any]:
    """Create sample metadata."""
    return {
        "title": "Test Adventure",
        "description": "A test narrative",
        "tags": ["test", "adventure"],
        "author": "Test Author",
        "created_at": datetime.now().isoformat(),
        "section_number": 1
    }

@pytest.fixture
def sample_narrator_model(model_factory, sample_metadata) -> NarratorModel:
    """Create a sample narrator model."""
    return model_factory.create_narrator_model(
        section_number=1,
        content=NarrativeContent(
            raw_text="This is a test narrative",
            formatted_text="This is a **test** narrative",
            choices={"1": "Go forward", "2": "Turn back"}
        ),
        metadata=sample_metadata
    )

@pytest.fixture
def sample_rules_model(model_factory) -> RulesModel:
    """Create sample rules model."""
    return model_factory.create_rules_model(
        section_number=1,
        needs_dice=True,
        dice_type=DiceType.COMBAT,
        conditions=[
            RuleCondition(text="Must have sword", item_required="sword"),
            RuleCondition(text="SKILL > 8", stat_check={"stat": "SKILL", "value": 8, "operator": ">"})
        ],
        choices=[
            Choice(
                text="Combat with troll",
                type=ChoiceType.DICE,
                dice_type=DiceType.COMBAT,
                dice_results={"success": 145, "failure": 278}
            )
        ]
    )

@pytest.fixture
def sample_decision_model(model_factory) -> DecisionModel:
    """Create sample decision model."""
    return model_factory.create_decision_model(
        section_number=1,
        decision_type=DecisionType.CHOICE,
        choices={"1": "Go forward", "2": "Turn back"},
        validation=ChoiceValidation(
            valid_choices=["1", "2"]
        )
    )

@pytest.fixture
def sample_trace_model(model_factory) -> TraceModel:
    """Create sample trace model."""
    return model_factory.create_trace_model(
        section_number=1,
        actions=[
            Action(
                type=ActionType.CHOICE,
                description="Player chose to go forward",
                timestamp=datetime.now()
            )
        ]
    )

@pytest.fixture
def sample_game_state(game_factory, sample_character, sample_metadata) -> GameState:
    """Create a sample game state."""
    return game_factory.create_game_state(
        session_id="test_session",
        game_id="test_game",
        section_number=1,
        character=sample_character,
        metadata=sample_metadata
    )

@pytest.mark.asyncio
async def test_story_graph_initialization(story_graph):
    """Test story graph initialization."""
    assert story_graph.config is not None
    assert story_graph.workflow_manager is not None
    assert story_graph.narrator_agent is not None
    assert story_graph.rules_agent is not None
    assert story_graph.decision_agent is not None
    assert story_graph.trace_agent is not None

@pytest.mark.asyncio
async def test_process_narrative_node(
    story_graph, mock_narrator_agent, 
    sample_narrator_model, sample_game_state
):
    """Test processing narrative node."""
    # Setup narrative processing
    mock_narrator_agent.process_narrative.return_value = sample_narrator_model
    
    # Process narrative node
    result = await story_graph.process_narrative_node(sample_game_state)
    
    # Verify result
    assert isinstance(result, NarratorModel)
    assert result.section_number == sample_game_state.section_number
    mock_narrator_agent.process_narrative.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_process_rules_node(
    story_graph, mock_rules_agent,
    sample_rules_model, sample_game_state
):
    """Test processing rules node."""
    # Setup rules processing
    mock_rules_agent.process_rules.return_value = sample_rules_model
    
    # Process rules node
    result = await story_graph.process_rules_node(sample_game_state)
    
    # Verify result
    assert isinstance(result, RulesModel)
    assert result.section_number == sample_game_state.section_number
    mock_rules_agent.process_rules.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_process_decision_node(
    story_graph, mock_decision_agent,
    sample_decision_model, sample_game_state
):
    """Test processing decision node."""
    # Setup decision processing
    mock_decision_agent.process_decision.return_value = sample_decision_model
    
    # Process decision node
    result = await story_graph.process_decision_node(sample_game_state)
    
    # Verify result
    assert isinstance(result, DecisionModel)
    assert result.section_number == sample_game_state.section_number
    mock_decision_agent.process_decision.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_process_trace_node(
    story_graph, mock_trace_agent,
    sample_trace_model, sample_game_state
):
    """Test processing trace node."""
    # Setup trace processing
    mock_trace_agent.process_trace.return_value = sample_trace_model
    
    # Process trace node
    result = await story_graph.process_trace_node(sample_game_state)
    
    # Verify result
    assert isinstance(result, TraceModel)
    assert result.section_number == sample_game_state.section_number
    mock_trace_agent.process_trace.assert_called_once_with(sample_game_state)

@pytest.mark.asyncio
async def test_process_workflow(
    story_graph, mock_workflow_manager,
    sample_game_state, sample_narrator_model,
    sample_rules_model, sample_decision_model
):
    """Test workflow processing."""
    # Setup workflow processing
    mock_workflow_manager.process_workflow.return_value = {
        "narrative": sample_narrator_model,
        "rules": sample_rules_model,
        "decision": sample_decision_model
    }
    
    # Process workflow
    result = await story_graph.process_workflow(sample_game_state)
    
    # Verify workflow
    assert isinstance(result, dict)
    assert "narrative" in result
    assert "rules" in result
    assert "decision" in result
    mock_workflow_manager.process_workflow.assert_called_once()

@pytest.mark.asyncio
async def test_process_invalid_state(story_graph, sample_game_state):
    """Test processing with invalid state."""
    # Create invalid state
    invalid_state = sample_game_state.model_copy()
    invalid_state.section_number = -1
    
    # Process invalid state
    with pytest.raises(ValueError):
        await story_graph.process_workflow(invalid_state)

@pytest.mark.asyncio
async def test_process_workflow_error(
    story_graph, mock_workflow_manager, sample_game_state
):
    """Test workflow processing with error."""
    # Setup error case
    mock_workflow_manager.process_workflow.side_effect = Exception("Processing error")
    
    # Process workflow
    with pytest.raises(StoryGraphError):
        await story_graph.process_workflow(sample_game_state)
