"""
Test module for game managers
This module contains unit tests for the different game managers.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import os
from managers.state_manager import StateManager
from managers.agent_manager import AgentManager
from managers.cache_manager import CacheManager
from managers.character_manager import CharacterManager
from models.game_state import GameState
from config.game_config import GameConfig

# Fixtures
@pytest.fixture
def game_config():
    return GameConfig()

@pytest.fixture
def state_manager(game_config):
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
    mock.create_initial_state = AsyncMock(return_value=initial_state)
    mock._get_default_trace = Mock(return_value=initial_state['trace'])
    mock.update_section_state = AsyncMock()
    mock.get_state = AsyncMock(return_value=initial_state)
    return mock

@pytest.fixture
def cache_manager(game_config):
    return CacheManager(config=game_config.options["cache_manager_config"])

@pytest.fixture
def character_manager(game_config):
    return CharacterManager(config=game_config.options["character_manager_config"])

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
    """Create mock agents for testing"""
    narrator = Mock()
    narrator.process_content = AsyncMock()
    narrator.process_content.return_value = AsyncIterator([{
        'content': '# Section 1\nTest content',
        'error': None
    }])

    rules = Mock()
    rules.process_rules = AsyncMock()
    rules.process_rules.return_value = AsyncIterator([{
        'needs_dice': False,
        'dice_type': None,
        'conditions': [],
        'next_sections': [2],
        'error': None
    }])

    decision = Mock()
    decision.process_decision = AsyncMock()
    decision.process_decision.return_value = AsyncIterator([{
        'choices': ['Option 1', 'Option 2'],
        'error': None
    }])

    return {
        'narrator': narrator,
        'rules': rules,
        'decision': decision
    }

@pytest.fixture
def agent_manager(mock_agents, game_config, state_manager):
    """Create AgentManager instance with mock dependencies"""
    return AgentManager(
        config=game_config.options["agent_manager_config"],
        narrator=mock_agents['narrator'],
        rules=mock_agents['rules'],
        decision=mock_agents['decision'],
        state_manager=state_manager
    )

# StateManager Tests
class TestStateManager:
    
    @pytest.mark.asyncio
    async def test_create_initial_state(self, state_manager):
        """Test that create_initial_state returns a valid initial state"""
        state = await state_manager.create_initial_state()
        
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
        mock_agents['narrator'].process_content.return_value = AsyncIterator([{
            'content': '# Section 1\nTest content',
            'error': None
        }])
        
        # Process state
        result = await agent_manager.process_narrator(initial_state)
        print(f"Actual result: {result}")
        
        # Verify the call was made with initial state
        mock_agents['narrator'].process_content.assert_called_once_with(initial_state)
        
        # Verify result contains both initial state and new content
        assert result["state"]["initial"] == "state"
        assert result["state"]["current_section"]["content"] == "test content"

    @pytest.mark.asyncio
    async def test_process_narrator_error(self, agent_manager, mock_agents):
        """Test narrator processing with error"""
        # Setup mock to raise exception
        mock_agents['narrator'].process_content.side_effect = Exception("Test error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_narrator(state)
        
        # Verify error message
        assert str(exc_info.value) == "Test error"
        
        # Verify the call was attempted
        mock_agents['narrator'].process_content.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_rules(self, agent_manager, mock_agents):
        """Test rules processing"""
        # Prepare test data
        initial_state = {'initial': 'state'}
        
        # Process state
        result = await agent_manager.process_rules(initial_state)
        
        # Verify the call was made with initial state
        mock_agents['rules'].process_rules.assert_called_once_with(initial_state)
        
        # Verify result contains both initial state and new rules
        assert result['state']['initial'] == 'state'
        assert result['state']['rules']['needs_dice'] is False

    @pytest.mark.asyncio
    async def test_process_rules_error(self, agent_manager, mock_agents):
        """Test rules processing with error"""
        # Setup mock to raise exception
        mock_agents['rules'].process_rules.side_effect = Exception("Rules error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_rules(state)
        
        # Verify error message
        assert str(exc_info.value) == "Rules error"
        
        # Verify the call was attempted
        mock_agents['rules'].process_rules.assert_called_once_with(state)

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
        
        mock_agents['decision'].process_decision.return_value = AsyncIterator([{
            'choices': ['Option 1', 'Option 2'],
            'error': None
        }])
        
        # Process state
        result = await agent_manager.process_decision(initial_state)
        
        # Verify the call was made with correct rules
        mock_agents['decision'].process_decision.assert_called_once_with({
            "state": {
                "rules": {
                    "some": "rules"
                }
            }
        })
        
        # Verify result contains decision with awaiting_action
        assert result['decision']['choices'] == ['Option 1', 'Option 2']

    @pytest.mark.asyncio
    async def test_process_decision_error(self, agent_manager, mock_agents):
        """Test decision processing with error"""
        # Setup mock to raise exception
        mock_agents['decision'].process_decision.side_effect = Exception("Decision error")
        
        # Test
        state = {'initial': 'state'}
        with pytest.raises(Exception) as exc_info:
            await agent_manager.process_decision(state)
        
        # Verify error message
        assert str(exc_info.value) == "Decision error"
        
        # Verify the call was attempted
        mock_agents['decision'].process_decision.assert_called_once_with(state)

    @pytest.mark.asyncio
    async def test_process_section(self, agent_manager, mock_agents, state_manager):
        """Test full section processing with parallel execution"""
        # Setup
        section_number = 1
        content = "test content"
        
        # Configure mocks
        mock_agents['narrator'].process_content.return_value = AsyncIterator([{
            'content': '# Section 1\nTest content',
            'error': None
        }])
        mock_agents['rules'].process_rules.return_value = AsyncIterator([{
            'needs_dice': False,
            'dice_type': None,
            'conditions': [],
            'next_sections': [2],
            'error': None
        }])
        mock_agents['decision'].process_decision.return_value = AsyncIterator([{
            'choices': ['Option 1', 'Option 2'],
            'error': None
        }])
        
        # Execute
        result = await agent_manager.process_section(section_number, content)
        
        # Verify the base state was created correctly
        expected_base_state = GameState(
            section_number=section_number,
            narrative={
                "number": section_number,
                "content": content,
                "choices": [],
                "stats": {}
            },
            needs_content=False
        ).model_dump()
        
        # Verify narrator and rules were called with the base state
        mock_agents['narrator'].process_content.assert_called_once()
        call_args = mock_agents['narrator'].process_content.call_args[0][0]
        assert call_args["section_number"] == expected_base_state["section_number"]
        assert call_args["narrative"]["content"] == expected_base_state["narrative"]["content"]
        
        mock_agents['rules'].process_rules.assert_called_once()
        call_args = mock_agents['rules'].process_rules.call_args[0][0]
        assert call_args["section_number"] == expected_base_state["section_number"]
        
        # Verify decision was called with combined state
        mock_agents['decision'].process_decision.assert_called_once()
        decision_call_args = mock_agents['decision'].process_decision.call_args[0][0]
        assert "rules" in decision_call_args
        assert decision_call_args["rules"]["needs_dice"] is False
        
        # Verify final result structure
        assert isinstance(result, dict)
        assert result["section_number"] == section_number
        assert "narrative" in result
        assert "rules" in result
        assert result["rules"]["needs_dice"] is False

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

# CharacterManager Tests
class TestCharacterManager:
    
    @pytest.mark.asyncio
    async def test_character_manager(self, character_manager):
        """Test character manager"""
        # Test
        result = await character_manager.get_character_stats()
        
        # Verify result
        assert isinstance(result, dict)
        assert 'Caractéristiques' in result
        assert result['Caractéristiques']['Habileté'] == 10
        assert result['Caractéristiques']['Chance'] == 5
