"""
Shared pytest configuration and fixtures
"""

import asyncio

import pytest


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    Required for long-running async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def backend_url():
    """
    Default backend URL for WebSocket tests.
    Can be overridden with environment variable.
    """
    import os

    return os.getenv("TEST_BACKEND_URL", "ws://localhost:8000/ws")
