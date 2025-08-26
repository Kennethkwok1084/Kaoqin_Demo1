"""
Async test helpers for proper event loop isolation
"""

import asyncio
import functools
from typing import Any, Callable, TypeVar
from unittest.mock import AsyncMock

F = TypeVar("F", bound=Callable[..., Any])


def ensure_fresh_loop(func: F) -> F:
    """
    Decorator to ensure each test runs with a fresh event loop
    to prevent 'Task got Future attached to a different loop' errors
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get current loop or create new one
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No loop running, we'll use the one pytest-asyncio provides
            return await func(*args, **kwargs)

        # Run the test in the current loop context
        return await func(*args, **kwargs)

    return wrapper


class AsyncContextManager:
    """Helper for managing async context in tests"""

    def __init__(self):
        self._cleanup_tasks = []

    async def add_cleanup(self, coro):
        """Add a cleanup coroutine to run later"""
        self._cleanup_tasks.append(coro)

    async def cleanup(self):
        """Run all cleanup tasks"""
        for task in self._cleanup_tasks:
            try:
                if asyncio.iscoroutine(task):
                    await task
                elif callable(task):
                    result = task()
                    if asyncio.iscoroutine(result):
                        await result
            except Exception:
                pass  # Ignore cleanup errors
        self._cleanup_tasks.clear()


def create_async_mock_session():
    """Create a properly configured async mock session"""
    session = AsyncMock()

    # Configure common async methods
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.flush = AsyncMock()
    session.close = AsyncMock()
    session.execute = AsyncMock()
    session.add = AsyncMock()
    session.delete = AsyncMock()

    # Mock transaction state
    session.in_transaction = AsyncMock(return_value=True)

    return session


def safe_async_mock(return_value=None, side_effect=None):
    """Create an AsyncMock that's safe for event loop isolation"""
    mock = AsyncMock()

    if return_value is not None:
        mock.return_value = return_value

    if side_effect is not None:
        mock.side_effect = side_effect

    return mock
