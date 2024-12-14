import pytest
import os
import sys
import pytest_asyncio
import asyncio

# Ajouter le répertoire racine au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest_asyncio.fixture(scope="function")
async def event_loop():
    """Create a new event loop for each test function."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def clean_event_bus():
    """Provide a clean event bus for each test."""
    from event_bus import EventBus
    event_bus = EventBus()
    yield event_bus
