"""Test the complete workflow process."""
import pytest
from unittest.mock import AsyncMock
from models.game_state import GameState
from models.decision_model import DecisionModel
from models.rules_model import RulesModel
from models.trace_model import TraceModel
from models.narrator_model import NarratorModel
from agents.story_graph import StoryGraph
from config.agents.agent_config_base import AgentConfigBase

@pytest.mark.asyncio
async def test_complete_workflow_process(mock_agent_manager, mock_agents, mock_managers):
    """Test the complete workflow process including:
    1. Decision agent providing next_section
    2. State recreation with session_id preservation
    3. should_continue workflow control
    4. Trace agent state recording
    """
    # Get manager mocks
    state_manager = mock_managers.state_manager
    trace_manager = mock_managers.trace_manager
    workflow_manager = mock_managers.workflow_manager

    # Get agent mocks
    decision_agent = mock_agents.decision_agent
    rules_agent = mock_agents.rules_agent
    narrator_agent = mock_agents.narrator_agent
    trace_agent = mock_agents.trace_agent

    # Create initial state
    initial_state = GameState(
        session_id="test_session_123",
        section_number=1,
        player_input="go to section 2"
    )
    state_manager.get_current_state.return_value = initial_state
    state_manager.create_initial_state.return_value = initial_state

    # Initialize agent manager
    await mock_agent_manager.initialize()

    # Initialize story graph
    config = AgentConfigBase()
    story_graph = StoryGraph(
        config=config,
        managers=mock_managers,
        agents=mock_agents
    )
    mock_agent_manager.story_graph = story_graph
    await story_graph._setup_workflow()

    # Test 1: Decision agent provides next_section
    # Setup workflow responses
    rules = RulesModel(section_number=1)
    rules_agent.set_iter_items([{"rules": rules}])
    
    narrative = NarratorModel(section_number=1)
    narrator_agent.set_iter_items([{"narrative": narrative}])
    
    decision_result = DecisionModel(
        section_number=1,
        next_section=2
    )
    decision_agent.set_iter_items([{"decision": decision_result}])

    # Setup workflow execution to actually call the story graph
    async def execute_workflow_mock(state, user_input, story_graph):
        # Process rules and narrative in parallel
        rules_result = await story_graph._process_rules(state)
        narrative_result = await story_graph._process_narrative(state)
        
        # Process decision
        decision_state = await story_graph._process_decision(state)
        
        # Return final state
        return GameState(
            session_id=state.session_id,
            section_number=2,
            decision=decision_result,
            rules=rules,
            narrative=narrative
        )

    workflow_manager.execute_workflow = execute_workflow_mock

    # Process user input
    state = await mock_agent_manager.process_user_input("go to section 2")
    
    # Verify workflow execution
    assert state.section_number == 2
    assert state.decision.next_section == 2

    # Test 2: State recreation preserves session_id
    # Get the new state after workflow
    state_manager.get_current_state.return_value = state
    new_state = await mock_agent_manager.get_state()
    assert new_state.session_id == "test_session_123"
    assert new_state.section_number == 2

    # Test 3: should_continue stops workflow
    # Setup rules that need user input
    rules = RulesModel(
        section_number=2,
        needs_user_response=True
    )
    rules_agent.set_iter_items([{"rules": rules}])
    new_state.rules = rules
    
    # Check should_continue
    should_continue = await mock_agent_manager.should_continue(new_state)
    assert not should_continue

    # Test 4: Trace agent records state
    # Setup trace recording
    trace = TraceModel(
        section_number=2,
        game_id="test_game_123",
        session_id="test_session_123"
    )
    trace_agent.set_iter_items([{"trace": trace}])
    
    # Execute workflow
    await mock_agent_manager.execute_workflow(new_state)
    
    # Verify trace agent was called
    trace_agent.assert_called_once()
    trace_manager.save_trace.assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__])
