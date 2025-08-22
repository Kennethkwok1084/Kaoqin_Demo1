#!/usr/bin/env python3
"""
Database configuration verification script.
Tests different database configurations and environments.
"""

import asyncio
import os
import sys
from typing import Any, Dict

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

# Import project modules
from app.core.config import settings
from app.core.database_compatibility import (
    get_test_database_url,
    should_use_postgresql_tests,
)
from app.models.base import Base


async def test_database_connection(engine_url: str, description: str) -> Dict[str, Any]:
    """Test database connection and basic operations."""
    print(f"\n--- Testing {description} ---")
    print(f"Database URL: {engine_url}")

    result = {
        "description": description,
        "url": engine_url,
        "connection_success": False,
        "tables_created": False,
        "error": None,
    }

    try:
        # Create engine
        if "sqlite" in engine_url:
            engine = create_async_engine(
                engine_url,
                echo=False,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            engine = create_async_engine(
                engine_url,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
            )

        # Test connection
        async with engine.begin() as conn:
            print("Database connection successful")
            result["connection_success"] = True

            # Try to create tables
            await conn.run_sync(Base.metadata.create_all)
            print("Tables created successfully")
            result["tables_created"] = True

            # Test a simple query
            from sqlalchemy import text

            query_result = await conn.execute(text("SELECT 1 as test"))
            test_value = query_result.scalar()
            print(f"Query test successful: {test_value}")

        await engine.dispose()
        print(f"{description} verification completed successfully")

    except Exception as e:
        print(f"{description} failed: {str(e)}")
        result["error"] = str(e)

    return result


async def main() -> int:
    """Main verification function."""
    print("Database Configuration Verification")
    print("=" * 50)

    # Test scenarios
    test_scenarios = []

    # Current configuration
    current_url = settings.DATABASE_URL
    test_scenarios.append((current_url, "Current Configuration"))

    # Test CI environment simulation
    os.environ["CI"] = "true"
    os.environ["GITHUB_ACTIONS"] = "true"
    ci_url = get_test_database_url()
    test_scenarios.append((ci_url, "CI Environment (SQLite)"))

    # Reset CI environment
    os.environ.pop("CI", None)
    os.environ.pop("GITHUB_ACTIONS", None)

    # Test local testing environment
    os.environ["TESTING"] = "true"
    testing_url = get_test_database_url()
    test_scenarios.append((testing_url, "Local Testing (SQLite)"))

    # Reset testing environment
    os.environ.pop("TESTING", None)

    # Test PostgreSQL if available (optional)
    os.environ["POSTGRES_TEST"] = "true"
    postgres_url = get_test_database_url()
    test_scenarios.append((postgres_url, "PostgreSQL Testing (if available)"))

    # Reset PostgreSQL test environment
    os.environ.pop("POSTGRES_TEST", None)

    # Run all tests
    results = []
    for url, description in test_scenarios:
        result = await test_database_connection(url, description)
        results.append(result)

    # Summary
    print("\n" + "=" * 50)
    print("VERIFICATION SUMMARY")
    print("=" * 50)

    successful = 0
    total = len(results)

    for result in results:
        status = "PASS" if result["connection_success"] else "FAIL"
        print(f"{status} {result['description']}")
        if result["error"]:
            print(f"    Error: {result['error']}")
        if result["connection_success"]:
            successful += 1

    print(f"\nSuccess Rate: {successful}/{total} ({successful / total * 100:.1f}%)")

    # Recommendations
    print("\nRECOMMENDATIONS")
    print("-" * 30)

    sqlite_working = any(
        r["connection_success"] and "sqlite" in r["url"].lower() for r in results
    )
    postgres_working = any(
        r["connection_success"] and "postgresql" in r["url"].lower() for r in results
    )

    if sqlite_working:
        print("SQLite is working - Good for CI/testing environments")
    else:
        print("SQLite issues detected - Check aiosqlite installation")

    if postgres_working:
        print("PostgreSQL is available - Good for integration testing")
    else:
        print("PostgreSQL not available - CI will use SQLite only")

    # Environment configuration status
    print("\nENVIRONMENT CONFIGURATION")
    print("-" * 30)
    print(f"CI Environment Detection: {os.getenv('CI', 'false')}")
    print(f"GitHub Actions Detection: {os.getenv('GITHUB_ACTIONS', 'false')}")
    print(f"Testing Mode: {os.getenv('TESTING', 'false')}")
    print(f"PostgreSQL Test Mode: {os.getenv('POSTGRES_TEST', 'false')}")
    print(f"Should Use PostgreSQL Tests: {should_use_postgresql_tests()}")

    if successful >= total - 1:  # Allow one failure (usually PostgreSQL)
        print("\nDatabase configuration is ready for CI/CD!")
        return 0
    else:
        print("\nDatabase configuration needs attention before CI/CD")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
