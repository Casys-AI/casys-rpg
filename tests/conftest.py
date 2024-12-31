"""Global test configuration and fixtures."""

import pytest
import os
import sys
import pytest_asyncio
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add root directory to PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AsyncIterMock:
    """Mock that returns an async iterator."""
    def __init__(self, items):
        self.items = items
        self._iter = iter(items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration

class AsyncMockWithIter(AsyncMock):
    """Mock that can return an async iterator."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._iter_items = []
        self._iter_mock = None

    def set_iter_items(self, items):
        """Set items to yield."""
        self._iter_items = items
        self._iter_mock = AsyncIterMock(items)
        self.ainvoke.return_value = self._iter_mock

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
    EventBus._subscribers = {}
    EventBus._history = []
    yield
    EventBus._subscribers = {}
    EventBus._history = []
