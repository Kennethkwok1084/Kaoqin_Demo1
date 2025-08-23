#!/usr/bin/env python3
"""
Database configuration validation script.
Tests various environment configurations to ensure database settings work correctly.
"""

import os
import sys


def test_configuration(name: str, env_vars: dict, expected_patterns: dict):
    """Test a specific configuration scenario."""
    print(f"\n=== Testing {name} ===")
    
    # Clear relevant environment variables
    for key in ['CI', 'GITHUB_ACTIONS', 'DATABASE_URL', 'DATABASE_URL_SYNC', 
                'POSTGRES_TEST', 'FORCE_SQLITE_TESTS', 'TESTING']:
        if key in os.environ:
            del os.environ[key]
    
    # Set test environment variables
    for key, value in env_vars.items():
        if value is not None:
            os.environ[key] = str(value)
    
    # Print environment
    for key in ['CI', 'GITHUB_ACTIONS', 'DATABASE_URL', 'POSTGRES_TEST', 'FORCE_SQLITE_TESTS']:
        print(f"  {key}: {os.environ.get(key, 'None')}")
    
    try:
        # Re-import to get fresh settings
        if 'app.core.config' in sys.modules:
            del sys.modules['app.core.config']
        if 'app.core.database_compatibility' in sys.modules:
            del sys.modules['app.core.database_compatibility']
        
        from app.core.config import settings
        from app.core.database_compatibility import get_test_database_url, should_use_postgresql_tests
        
        # Validate expectations
        success = True
        
        if 'database_url_contains' in expected_patterns:
            pattern = expected_patterns['database_url_contains']
            if pattern not in settings.DATABASE_URL:
                print(f"  FAIL: DATABASE_URL should contain '{pattern}', got: {settings.DATABASE_URL}")
                success = False
            else:
                print(f"  PASS: DATABASE_URL contains '{pattern}'")
        
        if 'test_url_contains' in expected_patterns:
            pattern = expected_patterns['test_url_contains']
            test_url = get_test_database_url()
            if pattern not in test_url:
                print(f"  FAIL: Test URL should contain '{pattern}', got: {test_url}")
                success = False
            else:
                print(f"  PASS: Test URL contains '{pattern}'")
        
        if 'should_use_postgresql' in expected_patterns:
            expected = expected_patterns['should_use_postgresql']
            actual = should_use_postgresql_tests()
            if actual != expected:
                print(f"  FAIL: should_use_postgresql should be {expected}, got: {actual}")
                success = False
            else:
                print(f"  PASS: should_use_postgresql is {expected}")
        
        return success
        
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all configuration tests."""
    print("Database Configuration Validation")
    print("=" * 50)
    
    sys.path.insert(0, '.')
    
    test_cases = [
        # Local development (using .env file)
        {
            'name': 'Local Development',
            'env_vars': {},
            'expected_patterns': {
                'database_url_contains': 'sqlite+aiosqlite',
                'test_url_contains': 'sqlite+aiosqlite',
                'should_use_postgresql': False
            }
        },
        
        # CI with explicit PostgreSQL URLs
        {
            'name': 'CI with PostgreSQL URLs',
            'env_vars': {
                'CI': 'true',
                'GITHUB_ACTIONS': 'true',
                'DATABASE_URL': 'postgresql+asyncpg://postgres:postgres@localhost:5432/test_attendence',
                'POSTGRES_TEST': 'true'
            },
            'expected_patterns': {
                'database_url_contains': 'postgres:postgres@localhost',
                'test_url_contains': 'postgres:postgres@localhost',
                'should_use_postgresql': True
            }
        },
        
        # CI with SQLite fallback
        {
            'name': 'CI with SQLite fallback',
            'env_vars': {
                'CI': 'true',
                'GITHUB_ACTIONS': 'true',
                'POSTGRES_TEST': 'false'
            },
            'expected_patterns': {
                'database_url_contains': 'postgres:postgres@localhost',
                'test_url_contains': 'sqlite+aiosqlite',
                'should_use_postgresql': False
            }
        },
        
        # Force SQLite tests
        {
            'name': 'Force SQLite Tests',
            'env_vars': {
                'FORCE_SQLITE_TESTS': 'true'
            },
            'expected_patterns': {
                'test_url_contains': 'sqlite+aiosqlite',
                'should_use_postgresql': False
            }
        },
        
        # Testing environment
        {
            'name': 'Testing Environment',
            'env_vars': {
                'TESTING': 'true'
            },
            'expected_patterns': {
                'test_url_contains': 'sqlite+aiosqlite',
                'should_use_postgresql': False
            }
        }
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for test_case in test_cases:
        if test_configuration(**test_case):
            success_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Passed: {success_count}/{total_count}")
    
    if success_count == total_count:
        print("All tests passed! Database configuration is working correctly.")
        sys.exit(0)
    else:
        print(f"Failed: {total_count - success_count} tests failed.")
        sys.exit(1)


if __name__ == '__main__':
    main()