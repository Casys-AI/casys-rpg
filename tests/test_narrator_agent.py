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
    
    # Créer quelques fichiers de test avec un contenu plus représentatif
    test_content = """La Forêt Mystérieuse

Vous arrivez à l'orée d'une forêt sombre. Les arbres semblent murmurer des secrets anciens.

Que souhaitez-vous faire ?

1. Explorer plus profondément dans la forêt
2. Retourner au village
3. Examiner les traces au sol"""

    with open(os.path.join(temp_dir, "1.md"), "w", encoding="utf-8") as f:
        f.write(test_content)
    
    yield temp_dir
    
    # Nettoyer après les tests
    shutil.rmtree(temp_dir)

@pytest.fixture
def narrator_agent(event_bus, content_dir):
    """Fixture pour le NarratorAgent."""
    cache_dir = os.path.join(content_dir, "cache")
    config = NarratorConfig(
        llm=ChatOpenAI(model="gpt-4o-mini", temperature=0),
        content_directory=content_dir,
        cache_directory=cache_dir
    )
    return NarratorAgent(config=config)

@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent):
    """Test que le NarratorAgent utilise le contenu du cache directement sans LLM"""
    section = 1
    
    # Créer un fichier dans le cache avec un contenu spécifique
    cache_path = os.path.join(narrator_agent.config.cache_directory, f"{section}_cached.md")
    cached_content = "This is a cached content that should be used directly"
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(cached_content)
    
    # L'appel devrait utiliser directement le contenu du cache sans le formater
    async for result in narrator_agent.ainvoke({"state": {"section_number": section, "use_cache": True}}):
        assert result["state"]["content"] == cached_content  # Le contenu doit être exactement le même
        assert result["state"]["source"] == "cache"  # La source doit être "cache"

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
        assert result["state"]["error"] == "Section 999 not found"  # Message d'erreur exact
        assert result["state"]["source"] == "not_found"  # Vérifie aussi la source

@pytest.mark.asyncio
async def test_narrator_agent_content_format(narrator_agent):
    """Test le format du contenu"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1}}):
        content = result["state"]["content"]
        assert isinstance(content, str)
        # Vérifie le formatage Markdown de base
        assert "#" in content  # Titre
        assert "**" in content  # Gras
        assert not "<h1>" in content  # Pas de HTML

@pytest.mark.asyncio
async def test_narrator_agent_content_formatting(narrator_agent, content_dir):
    """Test le formatage avec des références de section"""
    section = 2
    
    # Créer un fichier de test avec des références de section
    test_content = """Un titre simple

Un paragraphe avec du texte en *italique* et quelques mots importants.

1. Premier choix - aller à la section 3
2. Deuxième choix - aller à la section 4
3. Troisième choix - aller à la section 5"""
    
    with open(os.path.join(content_dir, f"{section}.md"), "w", encoding="utf-8") as f:
        f.write(test_content)
    
    async for result in narrator_agent.ainvoke({"state": {"section_number": section}}):
        content = result["state"]["content"]
        # Vérifie le formatage des références de section
        assert "[[3]]" in content and "[[4]]" in content and "[[5]]" in content

@pytest.mark.asyncio
async def test_narrator_section_selection(narrator_agent, event_bus):
    """Test que le NarratorAgent charge correctement la section 1"""
    async for result in narrator_agent.ainvoke({"state": {"section_number": 1}}):
        assert "state" in result
        assert "content" in result["state"]
        assert result["state"]["source"] in ["loaded", "cache"]

@pytest.mark.asyncio
async def test_narrator_agent_no_cache(narrator_agent, content_dir):
    """Test que le NarratorAgent process la section quand il n'y a pas de cache"""
    section = 3  # Utiliser une nouvelle section
    
    # Créer un fichier source sans cache
    test_content = """Test Section
    
    This is a test section with some *italic* text."""
    
    with open(os.path.join(content_dir, f"{section}.md"), "w", encoding="utf-8") as f:
        f.write(test_content)
    
    # Vérifier qu'il n'y a pas de cache initialement
    cache_path = os.path.join(narrator_agent.config.cache_directory, f"{section}_cached.md")
    assert not os.path.exists(cache_path)
    
    # L'appel devrait processer le contenu avec le LLM
    async for result in narrator_agent.ainvoke({"state": {"section_number": section}}):
        content = result["state"]["content"]
        assert content != test_content  # Le contenu doit être différent (formaté)
        assert "**" in content  # Doit contenir du formatage Markdown
        assert result["state"]["source"] in ["loaded", "cache"]  # La source peut être l'une ou l'autre
