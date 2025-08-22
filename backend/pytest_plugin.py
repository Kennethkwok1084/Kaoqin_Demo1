"""
Pytest plugin to set environment variables before any imports.
This ensures FORCE_SQLITE_TESTS is set early to avoid PostgreSQL asyncio issues.
"""
import os


def pytest_configure(config):
    """Configure pytest with early environment setup."""
    os.environ["FORCE_SQLITE_TESTS"] = "true"