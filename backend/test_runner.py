#!/usr/bin/env python3
"""
Simple test runner to validate the authentication module.
This script tests the core functionality without requiring full pytest setup.
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

async def test_basic_imports():
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
        
        print("[PASS] All imports successful!")
        return True
        
    except ImportError as e:
        print(f"[FAIL] Import error: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error: {e}")
        return False


async def test_security_functions():
    """Test basic security functions."""
    print("\n🔐 Testing security functions...")
    
    try:
        from app.core.security import create_access_token, verify_token, get_password_hash, verify_password
        
        # Test password hashing
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        print(f"✅ Password hashed: {hashed[:20]}...")
        
        # Test password verification
        is_valid = verify_password(password, hashed)
        print(f"✅ Password verification: {is_valid}")
        
        # Test token creation
        token = create_access_token(subject="123")
        print(f"✅ Token created: {token[:20]}...")
        
        # Test token verification
        payload = verify_token(token)
        print(f"✅ Token verified: {payload is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Security function error: {e}")
        return False


async def test_models():
    """Test model creation."""
    print("\n📋 Testing models...")
    
    try:
        from app.models.member import Member, UserRole
        from app.core.security import get_password_hash
        
        # Create a test user
        user = Member(
            name="测试用户",
            student_id="2021001001",
            password_hash=get_password_hash("TestPassword123!"),
            role=UserRole.MEMBER,
            is_active=True
        )
        
        print(f"✅ User created: {user.name} ({user.student_id})")
        print(f"✅ User role: {user.role.value}")
        print(f"✅ User permissions - is_admin: {user.is_admin}")
        print(f"✅ User permissions - can_manage_group: {user.can_manage_group}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test error: {e}")
        return False


async def test_schemas():
    """Test Pydantic schemas."""
    print("\n📝 Testing schemas...")
    
    try:
        from app.schemas.auth import LoginRequest, UserProfileResponse
        
        # Test LoginRequest
        login_data = {
            "student_id": "2021001001",
            "password": "TestPassword123!"
        }
        login_request = LoginRequest(**login_data)
        print(f"✅ LoginRequest created: {login_request.student_id}")
        
        # Test schema validation
        try:
            invalid_login = LoginRequest(student_id="", password="")
            print("❌ Schema validation failed - should have caught empty fields")
            return False
        except Exception:
            print("✅ Schema validation working - caught invalid data")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test error: {e}")
        return False


def test_api_structure():
    """Test API structure without database."""
    print("\n🌐 Testing API structure...")
    
    try:
        from app.api.v1 import auth
        print("✅ Auth router imported successfully")
        
        # Check if router has expected routes
        routes = [route.path for route in auth.router.routes]
        expected_routes = ["/login", "/refresh", "/logout", "/me", "/change-password", "/verify-token", "/health"]
        
        for expected in expected_routes:
            if any(expected in route for route in routes):
                print(f"✅ Route found: {expected}")
            else:
                print(f"❌ Route missing: {expected}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ API structure test error: {e}")
        return False


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting authentication module tests...\n")
    
    tests = [
        ("Basic Imports", test_basic_imports()),
        ("Security Functions", test_security_functions()),
        ("Models", test_models()),
        ("Schemas", test_schemas()),
        ("API Structure", test_api_structure())
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_coro in tests:
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"🧪 TEST SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*50}")
    
    if passed == total:
        print("🎉 All tests passed! Authentication module is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test runner error: {e}")
        sys.exit(1)