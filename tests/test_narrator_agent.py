import pytest
import pytest_asyncio
from agents.narrator_agent import NarratorAgent
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
    with open(os.path.join(temp_dir, "section_1.md"), "w") as f:
        f.write("Test content for section 1")
    
    with open(os.path.join(cache_dir, "1_cached.md"), "w") as f:
        f.write("Cached content for section 1")
    
    yield temp_dir
    
    # Nettoyer après les tests
    shutil.rmtree(temp_dir)

@pytest_asyncio.fixture
async def narrator_agent(event_bus, content_dir):
    return NarratorAgent(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        event_bus=event_bus,
        content_directory=content_dir
    )

@pytest.mark.asyncio
async def test_narrator_agent_basic(narrator_agent):
    """Test le fonctionnement de base"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1, "use_cache": False}}):
        assert "state" in result
        assert "content" in result["state"]
        assert isinstance(result["state"]["content"], str)
        assert "Test content for section 1" in result["state"]["content"]

@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent):
    """Test la mise en cache"""
    section = 1
    first_result = None
    second_result = None
    
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": True}}):
        first_result = result
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": True}}):
        second_result = result
    
    assert first_result["state"]["content"] == second_result["state"]["content"]
    assert second_result["state"]["source"] == "cache"

@pytest.mark.asyncio
async def test_narrator_agent_cache_directory(narrator_agent):
    """Test que le NarratorAgent utilise le contenu du cache s'il existe"""
    section = 1
    
    # Premier appel - devrait utiliser le fichier du cache
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": True}}):
        assert "Cached content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "cache"
    
    # Supprimer le fichier du cache
    os.remove(os.path.join(narrator_agent.content_directory, "cache", "1_cached.md"))
    
    # Deuxième appel - devrait utiliser le fichier normal
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": False}}):
        assert "Test content for section 1" in result["state"]["content"]
        assert result["state"]["source"] == "loaded"

@pytest.mark.asyncio
async def test_narrator_agent_events(narrator_agent, event_bus):
    """Test l'émission d'événements"""
    events = []
    async def event_listener(event):
        events.append(event)

    await event_bus.subscribe("content_generated", event_listener)
    async for _ in narrator_agent.ainvoke({"state": {"section_number": 1, "use_cache": False}}):
        pass
    
    assert len(events) > 0
    assert events[0].type == "content_generated"
    assert "content" in events[0].data

@pytest.mark.asyncio
async def test_narrator_agent_invalid_input(narrator_agent):
    """Test la gestion des entrées invalides"""
    async for result in narrator_agent.ainvoke({"state": {}}):
        assert "error" in result["state"]
        assert "Section number required" in result["state"]["error"]

@pytest.mark.asyncio
async def test_narrator_agent_section_not_found(narrator_agent):
    """Test la gestion des sections manquantes"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 999, "use_cache": False}}):
        assert "content" in result["state"]
        assert "Section 999 not found" in result["state"]["content"]
        assert result["state"]["source"] == "not_found"

@pytest.mark.asyncio
async def test_narrator_agent_content_format(narrator_agent):
    """Test le format du contenu"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1, "use_cache": False}}):
        assert "content" in result["state"]
        assert "formatted_content" in result["state"]
        assert isinstance(result["state"]["formatted_content"], str)

@pytest.mark.asyncio
async def test_narrator_agent_content_formatting(narrator_agent, content_dir):
    """Test le formatage du contenu"""
    # Créer un fichier de test avec du markdown
    test_content = "# Section Title\nThis is a test content with *formatting*"
    with open(os.path.join(content_dir, "section_2.md"), "w") as f:
        f.write(test_content)
        
    async for result in narrator_agent.ainvoke({"state": {"section_number": 2, "use_cache": False}}):
        assert result["state"]["content"] == test_content
        assert isinstance(result["state"]["formatted_content"], str)
        assert "# Section Title" in result["state"]["formatted_content"]
        assert "*formatting*" in result["state"]["formatted_content"]

@pytest.mark.asyncio
async def test_narrator_section_selection(narrator_agent, event_bus):
    """
    Test que le NarratorAgent :
    1. Affiche directement la section 1 au démarrage
    2. Utilise la section fournie par le DecisionAgent pour les autres sections
    """
    # Test section 1 (démarrage)
    state = {"section_number": 1}
    result = await narrator_agent.invoke({"state": state})
    
    assert result["state"]["section_number"] == 1
    assert "content" in result["state"]
    assert result["state"]["content"] is not None
    
    # Test autre section (venant du DecisionAgent)
    state = {
        "section_number": 2,
        "next_section": 3,  # Simuler une décision du DecisionAgent
        "analysis": "Test analysis"
    }
    
    result = await narrator_agent.invoke({"state": state})
    
    assert result["state"]["section_number"] == 3  # Doit utiliser next_section
    assert "content" in result["state"]
    assert result["state"]["content"] is not None
