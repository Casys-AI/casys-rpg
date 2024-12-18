"""
Tests for NarratorAgent
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace

from models.game_state import GameState
from models.narrator_model import NarratorModel, SourceType
from managers.cache_manager import CacheManager, CacheManagerConfig
from agents.narrator_agent import NarratorAgent
from config.agent_config import NarratorConfig

class MockResponse:
    def __init__(self, content):
        self.content = content

@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)

@pytest.fixture
def cache_config(temp_dir):
    """Crée la configuration du cache pour les tests."""
    return CacheManagerConfig(
        cache_dir=temp_dir,
        content_dir=os.path.join(temp_dir, "sections"),
        trace_dir=os.path.join(temp_dir, "trace")
    )

@pytest.fixture
def cache_manager(cache_config):
    """Crée un gestionnaire de cache pour les tests."""
    return CacheManager(config=cache_config)

@pytest.fixture
def narrator_config():
    """Crée la configuration du narrateur pour les tests."""
    return NarratorConfig(
        model_name="gpt-4o-mini",
        temperature=0.7,
        system_message="You are a skilled narrator for an interactive game book."
    )

@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    mock = AsyncMock()
    mock.ainvoke.return_value = MockResponse("Formatted Test content")
    return mock

@pytest.fixture
def narrator_agent(narrator_config, cache_manager, mock_llm):
    """Crée un agent narrateur pour les tests."""
    agent = NarratorAgent(
        config=narrator_config,
        cache_manager=cache_manager
    )
    agent.llm = mock_llm
    return agent

@pytest.mark.asyncio
async def test_narrator_agent_format_content(narrator_agent, mock_llm):
    """Test the content formatting with a mocked LLM."""
    raw_content = "Test content"
    
    # Configure mock for this specific test
    mock_llm.ainvoke.return_value = MockResponse(f"# Formatted Content\n\n{raw_content}")
    narrator_agent.config.llm = mock_llm
    
    formatted = await narrator_agent.format_content(raw_content)
    
    # Verify basic output requirements
    assert formatted is not None, "Formatted content should not be None"
    assert isinstance(formatted, str), "Formatted content should be a string"
    assert raw_content in formatted, "Formatted content should contain the original content"
    
    # Verify LLM was called correctly
    mock_llm.ainvoke.assert_called_once()
    messages = mock_llm.ainvoke.call_args[0][0]
    assert len(messages) == 2, "Should have system and human messages"
    assert messages[1].content == raw_content, "Human message should contain raw content"

@pytest.mark.asyncio
async def test_narrator_agent_read_section(narrator_agent, cache_manager, temp_dir, mock_llm):
    """Test la lecture d'une section depuis le fichier source."""
    section = 1
    raw_content = "Test section content"
    
    # Créer le fichier de section
    os.makedirs(os.path.join(temp_dir, "sections"), exist_ok=True)
    with open(os.path.join(temp_dir, "sections", f"{section}.md"), "w") as f:
        f.write(raw_content)
    
    # Test avec source=raw
    with patch('agents.narrator_agent.NarratorAgent._format_content', new_callable=AsyncMock) as mock_format:
        mock_format.return_value = f"# Section Test\n\n{raw_content}\n\nChoices:\n- [[1]] Option 1\n- [[2]] Option 2"
        
        state = GameState(
            section_number=section,
            narrative=NarratorModel(
                section_number=section,
                content="",
                source_type=SourceType.RAW
            )
        )
        
        async for result in narrator_agent.ainvoke(state.model_dump()):
            # Vérifie que le contenu est formaté en Markdown
            assert "# Section Test" in result["state"]["narrative"]["content"]
            assert "[[1]]" in result["state"]["narrative"]["content"]
            assert "[[2]]" in result["state"]["narrative"]["content"]
            assert raw_content in result["state"]["narrative"]["content"]
            assert result["state"]["narrative"]["source_type"] == SourceType.RAW
            
            # Vérifie que la section est mise en cache
            cached = cache_manager.get_section_from_cache(section)
            assert cached is not None
            assert raw_content in cached.content
            assert "# Section Test" in cached.content

@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent, cache_manager, mock_llm):
    """Test la lecture d'une section depuis le cache."""
    section = 1
    cached_content = "Cached content"
    
    # Créer une entrée dans le cache
    cache_section = NarratorModel(
        section_number=section,
        content=cached_content,
        source_type=SourceType.CACHED
    )
    cache_manager.save_section_to_cache(section, cache_section)
    
    # Test avec source=cache
    state = GameState(
        section_number=section,
        narrative=NarratorModel(
            section_number=section,
            content="",
            source_type=SourceType.CACHED
        )
    )
    
    async for result in narrator_agent.ainvoke(state.model_dump()):
        # Vérifie que le contenu vient du cache
        assert result["state"]["narrative"]["content"] == cached_content
        assert result["state"]["narrative"]["source_type"] == SourceType.CACHED

@pytest.mark.asyncio
async def test_narrator_agent_section_not_found(narrator_agent, mock_llm):
    """Test la gestion d'une section inexistante."""
    section = 999  # Section qui n'existe pas
    
    state = GameState(
        section_number=section,
        narrative=NarratorModel(
            section_number=section,
            content="",
            source_type=SourceType.RAW
        )
    )
    
    async for result in narrator_agent.ainvoke(state.model_dump()):
        # Vérifie que l'erreur est bien gérée
        assert result["state"]["narrative"]["error"] is not None
        assert "Section not found" in result["state"]["narrative"]["error"]
