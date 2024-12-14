import pytest
import pytest_asyncio
from agents.narrator_agent import NarratorAgent
from event_bus import EventBus, Event
from langchain_openai import ChatOpenAI

@pytest_asyncio.fixture
async def event_bus():
    return EventBus()

@pytest_asyncio.fixture
async def narrator_agent(event_bus):
    return NarratorAgent(
        llm=ChatOpenAI(model="gpt-4o-mini"),
        event_bus=event_bus
    )

@pytest.mark.asyncio
async def test_narrator_agent_basic(narrator_agent):
    """Test le fonctionnement de base"""
    result = await narrator_agent.ainvoke({"section_number": 1})
    assert "content" in result
    assert isinstance(result["content"], str)

@pytest.mark.asyncio
async def test_narrator_agent_cache(narrator_agent):
    """Test la mise en cache"""
    section = 1
    result1 = await narrator_agent.ainvoke({"section_number": section})
    result2 = await narrator_agent.ainvoke({"section_number": section})
    assert result1 == result2

@pytest.mark.asyncio
async def test_narrator_agent_events(narrator_agent, event_bus):
    """Test l'émission d'événements"""
    events = []
    async def event_listener(event):
        events.append(event)

    await event_bus.subscribe("content_generated", event_listener)
    await narrator_agent.ainvoke({"section_number": 1})
    assert len(events) > 0
    assert events[0].type == "content_generated"

@pytest.mark.asyncio
async def test_narrator_agent_invalid_input(narrator_agent):
    """Test la gestion des entrées invalides"""
    result = await narrator_agent.ainvoke({})
    assert "error" in result

@pytest.mark.asyncio
async def test_narrator_agent_section_not_found(narrator_agent):
    """Test la gestion des sections manquantes"""
    result = await narrator_agent.ainvoke({"section_number": 999})
    assert "content" in result

@pytest.mark.asyncio
async def test_narrator_agent_content_format(narrator_agent):
    """Test le format du contenu"""
    result = await narrator_agent.ainvoke({"section_number": 1})
    assert "content" in result
    assert "formatted_content" in result

@pytest.mark.asyncio
async def test_narrator_agent_content_formatting(narrator_agent):
    """Test le formatage du contenu par le NarratorAgent"""
    test_content = "# Section Title\nThis is a test content with *formatting*"
    result = await narrator_agent.ainvoke({
        "section_number": 1,
        "content": test_content
    })
    
    assert isinstance(result, dict)
    assert "formatted_content" in result
    assert result["formatted_content"] is not None
    assert "*formatting*" in result["formatted_content"]
