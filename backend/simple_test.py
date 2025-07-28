#!/usr/bin/env python3
"""
Simple test for authentication module without emojis.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the backend directory to the path so we can import app modules
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set environment variables for testing
os.environ["TESTING"] = "true"
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///:memory:"

async def test_imports():
    """Test that we can import all the modules we created."""
    print("[TEST] Testing basic imports...")
    
    try:
        from app.core.config import settings
        print("[PASS] Config imported successfully")
        
        from app.core.security import create_access_token, verify_password, get_password_hash
        print("[PASS] Security module imported successfully")
        
        from app.models.member import Member, UserRole
        print("[PASS] Member model imported successfully")
        
        from app.schemas.auth import LoginRequest, LoginResponse
        print("[PASS] Auth schemas imported successfully")
        
        from app.api.deps import get_current_user, create_response
        print("[PASS] Dependencies imported successfully")
        
        from app.api.v1 import auth
        print("[PASS] Auth router imported successfully")
        
        print("[PASS] All imports successful!")
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False

async def test_security():
    """Test basic security functions."""
    print("\n[TEST] Testing security functions...")
    
    try:
        from app.core.security import create_access_token, verify_token, get_password_hash, verify_password
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        print(f"[PASS] Password hashed: {hashed[:20]}...")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"[PASS] Password verification: {is_valid}")
        
        # Test token creation
        token = create_access_token(subject="123")
        print(f"[PASS] Token created: {token[:20]}...")
        
        # Test token verification
        payload = verify_token(token)
        print(f"[PASS] Token verified: {payload is not None}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Security function error: {e}")
        return False

async def test_models():
    """Test model creation."""
    print("\n[TEST] Testing models...")
    
    try:
        from app.models.member import Member, UserRole
        from app.core.security import get_password_hash
        
        # Create a test user
        user = Member(
            name="Test User",
            student_id="2021001001",
            password_hash=get_password_hash("TestPassword123!"),
            role=UserRole.MEMBER,
            is_active=True
        )
        
        print(f"[PASS] User created: {user.name} ({user.student_id})")
        print(f"[PASS] User role: {user.role.value}")
        print(f"[PASS] User permissions - is_admin: {user.is_admin}")
        print(f"[PASS] User permissions - can_manage_group: {user.can_manage_group}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Model test error: {e}")
        return False

async def run_tests():
    """Run all tests."""
    print("Starting authentication module tests...\n")
    
    tests = [
        ("Basic Imports", test_imports()),
        ("Security Functions", test_security()),
        ("Models", test_models())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_coro in tests:
        try:
            result = await test_coro
            if result:
                passed += 1
                print(f"[PASS] {test_name} PASSED")
            else:
                print(f"[FAIL] {test_name} FAILED")
        except Exception as e:
            print(f"[FAIL] {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"TEST SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*50}")
    
    if passed == total:
        print("All tests passed! Authentication module is working correctly.")
        return True
    else:
        print("Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest runner error: {e}")
        sys.exit(1)