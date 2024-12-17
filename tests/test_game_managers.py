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
    mock.emit_agent_result = AsyncMock()
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
    narrator.ainvoke = AsyncMock(side_effect=lambda x: AsyncIterator([
        {'content': 'test content'}
    ]))
    
    # Rules mock setup
    rules = AsyncMock()
    rules.ainvoke = AsyncMock(side_effect=lambda x: AsyncIterator([
        {'rules': {'needs_dice': True}}
    ]))
    
    # Decision mock setup
    decision = AsyncMock()
    decision.ainvoke = AsyncMock(side_effect=lambda x: AsyncIterator([
        {'decision': {'choice': 'A'}}
    ]))
    
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
    async def test_process_narrator_success(self, agent_manager, mock_agents, state_manager, event_bus):
        """Test successful narrator processing"""
        # Prepare test data
        initial_state = {'initial': 'state'}
        event_bus.get_state = AsyncMock(return_value=initial_state)
        
        # Process state
        result = await agent_manager.process_narrator(initial_state)
        
        # Verify the call was made with initial state
        mock_agents['narrator'].ainvoke.assert_called_once_with(initial_state)
        
        # Verify event was emitted
        event_bus.emit_agent_result.assert_called_with("narrator_updated", {'content': 'test content'})
        
        # Verify result contains both initial state and new content
        assert result['initial'] == 'state'
        assert result['content'] == 'test content'

    @pytest.mark.asyncio
    async def test_process_narrator_error(self, agent_manager, mock_agents, event_bus):
        """Test narrator processing with error"""
        # Setup mock to raise exception
        mock_agents['narrator'].ainvoke.side_effect = Exception("Test error")
        
        # Test
        state = {'initial': 'state'}
        result = await agent_manager.process_narrator(state)
        
        # Verify error handling
        assert 'error' in result
        assert isinstance(result['error'], str)
        assert 'Test error' in result['error']

    @pytest.mark.asyncio
    async def test_process_rules(self, agent_manager, mock_agents, event_bus):
        """Test rules processing"""
        # Prepare test data
        initial_state = {'initial': 'state'}
        
        # Process state
        result = await agent_manager.process_rules(initial_state)
        
        # Verify the call was made with initial state
        mock_agents['rules'].ainvoke.assert_called_once_with(initial_state)
        
        # Verify event was emitted
        event_bus.emit_agent_result.assert_called_with("rules_updated", {'rules': {'needs_dice': True}})
        
        # Verify result contains both initial state and new rules
        assert result['initial'] == 'state'
        assert result['rules']['needs_dice'] is True

    @pytest.mark.asyncio
    async def test_process_decision(self, agent_manager, mock_agents, event_bus):
        """Test decision processing"""
        # Prepare test data
        initial_state = {'rules': {'some': 'rules'}}
        
        # Process state
        result = await agent_manager.process_decision(initial_state)
        
        # Verify the call was made with correct rules
        mock_agents['decision'].ainvoke.assert_called_once_with({'rules': {'some': 'rules'}})
        
        # Verify event was emitted
        event_bus.emit_agent_result.assert_called_with("decision_updated", {'decision': {'choice': 'A', 'awaiting_action': 'choice'}})
        
        # Verify result contains decision with awaiting_action
        assert result['decision']['choice'] == 'A'
        assert result['decision']['awaiting_action'] == 'choice'

    @pytest.mark.asyncio
    async def test_process_section(self, agent_manager, mock_agents, event_bus, state_manager):
        """Test full section processing with parallel execution"""
        # Prepare test data
        section_number = 1
        content = "Test content"
        initial_state = {'section_number': section_number, 'content': content}
        event_bus.get_state = AsyncMock(return_value=initial_state)
        
        # Process section
        result = await agent_manager.process_section(section_number, content)
        
        # Verify state was updated
        state_manager.update_section_state.assert_called_once_with(section_number, content)
        
        # Verify both narrator and rules were called with initial state
        mock_agents['narrator'].ainvoke.assert_called_once_with(initial_state)
        mock_agents['rules'].ainvoke.assert_called_once_with(initial_state)
        
        # Verify decision was called after both narrator and rules
        mock_agents['decision'].ainvoke.assert_called_once()
        
        # Verify events were emitted in any order
        event_bus.emit_agent_result.assert_any_call("narrator_updated", {'content': 'test content'})
        event_bus.emit_agent_result.assert_any_call("rules_updated", {'rules': {'needs_dice': True}})

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
