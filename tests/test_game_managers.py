"""
Test module for game managers
This module contains unit tests for the different game managers.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import os
from managers.game_managers import StateManager, AgentManager, CacheManager, EventManager
from event_bus import EventBus, Event
from agents.models import GameState

# Fixtures
@pytest.fixture
def event_bus():
    mock = Mock(spec=EventBus)
    mock.emit = AsyncMock()
    mock.update_state = AsyncMock()
    mock.get_state = AsyncMock()
    return mock

@pytest.fixture
def state_manager(event_bus):
    mock = Mock(spec=StateManager)
    initial_state = {
        'section_number': 1,
        'needs_content': True,
        'trace': {
            'stats': {
                'Caractéristiques': {
                    'Habileté': 10,
                    'Chance': 5,
                    'Endurance': 8
                },
                'Inventaire': {
                    'Objets': ['Épée', 'Bouclier']
                },
                'Ressources': {
                    'Or': 100,
                    'Gemme': 5
                }
            },
            'history': []
        }
    }
    mock.initialize_state = AsyncMock(return_value=initial_state)
    mock._get_default_trace = Mock(return_value=initial_state['trace'])
    mock.update_section_state = AsyncMock()
    mock.get_state = AsyncMock(return_value=initial_state)
    return mock

@pytest.fixture
def cache_manager():
    return CacheManager(cache_dir="test_cache")

@pytest.fixture
def event_manager(event_bus):
    return EventManager(event_bus)

class AsyncIterator:
    """Helper class to simulate async iterators in tests"""
    def __init__(self, items):
        self.items = items.copy()  # Make a copy of items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)

@pytest.fixture
def mock_agents():
    # Narrator mock setup
    narrator = AsyncMock()
    narrator.ainvoke = AsyncMock()  # On laisse le return_value être configuré par le test
    
    # Rules mock setup
    rules = AsyncMock()
    rules.ainvoke = AsyncMock(return_value={
        "state": {
            "initial": "state",
            "rules": {
                "needs_dice": True,
                "dice_type": None,
                "conditions": [],
                "next_sections": [],
                "rules_summary": None,
                "raw_content": "",
                "choices": []
            }
        }
    })
    
    # Decision mock setup
    decision = AsyncMock()
    decision.ainvoke = AsyncMock(return_value={
        "decision": {
            "choice": "A",
            "awaiting_action": "choice"
        }
    })
    
    # Trace mock
    trace = AsyncMock()
    
    return {
        'narrator': narrator,
        'rules': rules,
        'decision': decision,
        'trace': trace
    }

@pytest.fixture
def agent_manager(mock_agents, event_bus, state_manager):
    return AgentManager(
        mock_agents['narrator'],
        mock_agents['rules'],
        mock_agents['decision'],
        mock_agents['trace'],
        event_bus,
        state_manager
    )

# StateManager Tests
class TestStateManager:
    
    @pytest.mark.asyncio
    async def test_initialize_state(self, state_manager):
        """Test that initialize_state returns a valid initial state"""
        state = await state_manager.initialize_state()
        
        # Verify state structure
        assert isinstance(state, dict)
        assert state['section_number'] == 1
        assert state['needs_content'] is True
        assert 'trace' in state
        assert 'stats' in state['trace']
        
        # Verify character stats
        stats = state['trace']['stats']
        assert 'Caractéristiques' in stats
        assert stats['Caractéristiques']['Habileté'] == 10
        assert stats['Caractéristiques']['Chance'] == 5
        
        # Verify inventory
        assert 'Inventaire' in stats
        assert 'Épée' in stats['Inventaire']['Objets']

    def test_get_default_trace(self, state_manager):
        """Test that _get_default_trace returns correct structure"""
        trace = state_manager._get_default_trace()
        
        assert isinstance(trace, dict)
        assert 'stats' in trace
        assert 'history' in trace
        assert isinstance(trace['history'], list)

# AgentManager Tests
class TestAgentManager:
    
    @pytest.mark.asyncio
    async def test_process_narrator_success(self, agent_manager, mock_agents, state_manager):
        """Test successful narrator processing"""
        # Prepare test data
        initial_state = {"state": {"initial": "state"}}
        mock_result = {
            "state": {
                "initial": "state",
                "current_section": {
                    "content": "test content"
                }
            }
        }
        print(f"\nMock configured to return: {mock_result}")
        mock_agents['narrator'].ainvoke.return_value = mock_result
        
        # Process state
        result = await agent_manager.process_narrator(initial_state)
        print(f"Actual result: {result}")
        
        # Verify the call was made with initial state
        mock_agents['narrator'].ainvoke.assert_called_once_with(initial_state)
        
        # Verify result contains both initial state and new content
        assert result["state"]["initial"] == "state"
        assert result["state"]["current_section"]["content"] == "test content"

    @pytest.mark.asyncio
    async def test_process_narrator_error(self, agent_manager, mock_agents):
        """Test narrator processing with error"""
        # Setup mock to raise exception
        mock_agents['narrator'].ainvoke.side_effect = Exception("Test error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_narrator(state)
        
        # Verify error message
        assert str(exc_info.value) == "Test error"
        
        # Verify the call was attempted
        mock_agents['narrator'].ainvoke.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_rules(self, agent_manager, mock_agents):
        """Test rules processing"""
        # Prepare test data
        initial_state = {'initial': 'state'}
        
        # Process state
        result = await agent_manager.process_rules(initial_state)
        
        # Verify the call was made with initial state
        mock_agents['rules'].ainvoke.assert_called_once_with(initial_state)
        
        # Verify result contains both initial state and new rules
        assert result['state']['initial'] == 'state'
        assert result['state']['rules']['needs_dice'] is True

    @pytest.mark.asyncio
    async def test_process_rules_error(self, agent_manager, mock_agents):
        """Test rules processing with error"""
        # Setup mock to raise exception
        mock_agents['rules'].ainvoke.side_effect = Exception("Rules error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_rules(state)
        
        # Verify error message
        assert str(exc_info.value) == "Rules error"
        
        # Verify the call was attempted
        mock_agents['rules'].ainvoke.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_decision(self, agent_manager, mock_agents):
        """Test decision processing"""
        # Prepare test data
        initial_state = {
            "state": {
                "rules": {
                    "some": "rules"
                }
            }
        }
        
        mock_agents['decision'].ainvoke.return_value = {
            "decision": {
                "choice": "A",
                "awaiting_action": "choice"
            }
        }
        
        # Process state
        result = await agent_manager.process_decision(initial_state)
        
        # Verify the call was made with correct rules
        mock_agents['decision'].ainvoke.assert_called_once_with({
            "state": {
                "rules": {
                    "some": "rules"
                }
            }
        })
        
        # Verify result contains decision with awaiting_action
        assert result['decision']['choice'] == 'A'
        assert result['decision']['awaiting_action'] == 'choice'

    @pytest.mark.asyncio
    async def test_process_decision_error(self, agent_manager, mock_agents):
        """Test decision processing with error"""
        # Setup mock to raise exception
        mock_agents['decision'].ainvoke.side_effect = Exception("Decision error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_decision(state)
        
        # Verify error message
        assert str(exc_info.value) == "Decision error"
        
        # Verify the call was attempted
        mock_agents['decision'].ainvoke.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_section(self, agent_manager, mock_agents, state_manager):
        """Test full section processing with parallel execution"""
        # Setup
        section_number = 1
        content = "test content"
        
        # Configure mocks
        mock_agents['narrator'].ainvoke.return_value = {
            "state": {
                "content": "formatted test content"
            }
        }
        mock_agents['rules'].ainvoke.return_value = {
            "state": {
                "rules": {
                    "needs_dice": True,
                    "dice_type": None,
                    "conditions": [],
                    "next_sections": [],
                    "rules_summary": None
                }
            }
        }
        mock_agents['decision'].ainvoke.return_value = {
            "state": {
                "decision": {
                    "awaiting_action": "choice",
                    "choices": []
                }
            }
        }
        
        # Execute
        result = await agent_manager.process_section(section_number, content)
        
        # Verify the base state was created correctly
        expected_base_state = GameState(
            section_number=section_number,
            current_section={
                "number": section_number,
                "content": content,
                "choices": [],
                "stats": {}
            },
            needs_content=False
        ).model_dump()
        
        # Verify narrator and rules were called with the base state
        mock_agents['narrator'].ainvoke.assert_called_once()
        call_args = mock_agents['narrator'].ainvoke.call_args[0][0]
        assert call_args["section_number"] == expected_base_state["section_number"]
        assert call_args["current_section"]["content"] == expected_base_state["current_section"]["content"]
        
        mock_agents['rules'].ainvoke.assert_called_once()
        call_args = mock_agents['rules'].ainvoke.call_args[0][0]
        assert call_args["section_number"] == expected_base_state["section_number"]
        
        # Verify decision was called with combined state
        mock_agents['decision'].ainvoke.assert_called_once()
        decision_call_args = mock_agents['decision'].ainvoke.call_args[0][0]
        assert "rules" in decision_call_args
        assert decision_call_args["rules"]["needs_dice"] is True
        
        # Verify final result structure
        assert isinstance(result, dict)
        assert result["section_number"] == section_number
        assert "current_section" in result
        assert "rules" in result
        assert result["rules"]["needs_dice"] is True

# CacheManager Tests
class TestCacheManager:
    
    def setup_method(self):
        """Setup test environment"""
        os.makedirs("test_cache", exist_ok=True)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        if os.path.exists("test_cache"):
            shutil.rmtree("test_cache")
    
    def test_check_section_cache(self, cache_manager):
        """Test cache checking"""
        # Create test cache file
        with open(os.path.join("test_cache", "1_cached.md"), "w") as f:
            f.write("test content")
            
        # Test
        assert cache_manager.check_section_cache(1) is True
        assert cache_manager.check_section_cache(2) is False
    
    def test_get_cache_path(self, cache_manager):
        """Test cache path generation"""
        path = cache_manager.get_cache_path(1)
        assert path == os.path.join("test_cache", "1_cached.md")

# EventManager Tests
class TestEventManager:
    
    @pytest.mark.asyncio
    async def test_emit_game_event(self, event_manager, event_bus):
        """Test game event emission"""
        # Setup mock
        event_bus.emit = AsyncMock()
        
        # Test
        await event_manager.emit_game_event("test_event", {"data": "test"})
        
        # Verify
        event_bus.emit.assert_called_once()
        call_args = event_bus.emit.call_args[0][0]
        assert isinstance(call_args, Event)
        assert call_args.type == "test_event"
        assert call_args.data == {"data": "test"}
    
    def test_truncate_for_log(self, event_manager):
        """Test log truncation"""
        # Test short content
        short = "short content"
        assert event_manager.truncate_for_log(short) == short
        
        # Test long content
        long = "x" * 150
        truncated = event_manager.truncate_for_log(long)
        assert len(truncated) == 103  # 100 chars + "..."
        assert truncated.endswith("...")
