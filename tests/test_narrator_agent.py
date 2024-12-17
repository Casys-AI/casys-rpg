import pytest
import pytest_asyncio
from agents.narrator_agent import NarratorAgent, NarratorConfig
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI
import os
import tempfile
import shutil

@pytest_asyncio.fixture
async def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def content_dir():
    # Créer un répertoire temporaire pour les tests
    temp_dir = tempfile.mkdtemp()
    
    # Créer le dossier cache
    cache_dir = os.path.join(temp_dir, "cache")
    os.makedirs(cache_dir)
    
    # Créer quelques fichiers de test
    test_content = "Test content for section 1"
    with open(os.path.join(temp_dir, "1.md"), "w") as f:
        f.write(test_content)
    
    with open(os.path.join(cache_dir, "1_cached.md"), "w") as f:
        f.write(test_content)
    
    yield temp_dir
    
    # Nettoyer après les tests
    shutil.rmtree(temp_dir)

@pytest.fixture
def narrator_agent(event_bus, content_dir):
    """Fixture pour le NarratorAgent."""
    config = NarratorConfig(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        content_directory=content_dir
    )
    return NarratorAgent(config=config)

@pytest.mark.asyncio
async def test_narrator_agent_basic(narrator_agent):
    """Test le fonctionnement de base"""
    section = 1
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": False}}):
        assert "content" in result["state"]
        assert "Test content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "loaded"

@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent):
    """Test la mise en cache"""
    section = 1
    
    # Premier appel - devrait charger depuis le fichier
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": False}}):
        assert "Test content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "loaded"
    
    # Deuxième appel - devrait utiliser le cache
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": True}}):
        assert "Test content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "cache"

@pytest.mark.asyncio
async def test_narrator_agent_cache_directory(narrator_agent):
    """Test que le NarratorAgent utilise le contenu du cache s'il existe"""
    section = 1
    
    # Premier appel - devrait charger depuis le fichier
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": False}}):
        assert "Test content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "loaded"

@pytest.mark.asyncio
async def test_narrator_agent_invalid_input(narrator_agent):
    """Test la gestion des entrées invalides"""
    async for result in narrator_agent.ainvoke({"state": {}}):
        assert "error" in result["state"]

@pytest.mark.asyncio
async def test_narrator_agent_section_not_found(narrator_agent):
    """Test la gestion des sections manquantes"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 999, "use_cache": False}}):
        assert "error" in result["state"]
        assert "Content not found for section 999" in result["state"]["error"]

@pytest.mark.asyncio
async def test_narrator_agent_content_format(narrator_agent):
    """Test le format du contenu"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1}}):
        content = result["state"]["content"]
        assert isinstance(content, str)
        assert "<h1>" in content or "<p>" in content

@pytest.mark.asyncio
async def test_narrator_agent_content_formatting(narrator_agent, content_dir):
    """Test le formatage du contenu"""
    # Créer un fichier de test avec du markdown
    test_content = "# Test Title\n\nTest paragraph with *italic* text"
    with open(os.path.join(content_dir, "format_test.md"), "w") as f:
        f.write(test_content)
    
    async for result in narrator_agent.ainvoke({"state": {"section_number": "format_test"}}):
        content = result["state"]["content"]
        assert "<h1>" in content
        assert "<em>" in content or "<i>" in content
        assert "<p>" in content

@pytest.mark.asyncio
async def test_narrator_section_selection(narrator_agent, event_bus):
    """Test que le NarratorAgent charge correctement la section 1"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1}}):
        assert "state" in result
        assert "content" in result["state"]
        assert result["state"]["source"] in ["loaded", "cache"]
