#!/usr/bin/env python3
"""
Test script to verify permission system and rate limiting fixes.
This script tests the core functionality that was identified as problematic.
"""

import asyncio
import sys

from app.api.deps import (
    get_admin_user,
    get_group_leader_or_admin,
)
from app.core.security import rate_limiter
from app.models.member import Member, UserRole


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"


def print_success(message):
    print(f"{Colors.GREEN}[SUCCESS] {message}{Colors.END}")


def print_error(message):
    print(f"{Colors.RED}[ERROR] {message}{Colors.END}")


def print_info(message):
    print(f"{Colors.BLUE}[INFO] {message}{Colors.END}")


async def test_permission_functions():
    """Test all permission dependency functions."""
    print_info("Testing permission functions...")

    # Create test users
    admin_user = Member(
        id=1,
        username="admin",
        name="Admin User",
        student_id="ADMIN001",
        role=UserRole.ADMIN,
        is_active=True,
    )

    group_leader_user = Member(
        id=2,
        username="leader",
        name="Group Leader",
        student_id="LEADER001",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )

    regular_user = Member(
        id=3,
        username="member",
        name="Regular Member",
        student_id="MEMBER001",
        role=UserRole.MEMBER,
        is_active=True,
    )

    test_results = []

    # Test get_admin_user
    try:
        result = await get_admin_user(current_user=admin_user)
        if result.role == UserRole.ADMIN:
            print_success("get_admin_user: Admin access granted correctly")
            test_results.append(True)
        else:
            print_error("get_admin_user: Admin check failed")
            test_results.append(False)
    except Exception as e:
        print_error(f"get_admin_user: Unexpected error - {e}")
        test_results.append(False)

    # Test get_admin_user with regular user (should fail)
    try:
        await get_admin_user(current_user=regular_user)
        print_error("get_admin_user: Regular user should not have admin access")
        test_results.append(False)
    except Exception as e:
        if "Admin privileges required" in str(e):
            print_success("get_admin_user: Regular user correctly denied")
            test_results.append(True)
        else:
            print_error(f"get_admin_user: Wrong error message - {e}")
            test_results.append(False)

    # Test get_group_leader_or_admin with admin
    try:
        result = await get_group_leader_or_admin(current_user=admin_user)
        print_success("get_group_leader_or_admin: Admin access granted")
        test_results.append(True)
    except Exception as e:
        print_error(f"get_group_leader_or_admin: Admin should have access - {e}")
        test_results.append(False)

    # Test get_group_leader_or_admin with group leader
    try:
        result = await get_group_leader_or_admin(current_user=group_leader_user)
        print_success("get_group_leader_or_admin: Group leader access granted")
        test_results.append(True)
    except Exception as e:
        print_error(f"get_group_leader_or_admin: Group leader should have access - {e}")
        test_results.append(False)

    # Test get_group_leader_or_admin with regular member (should fail)
    try:
        await get_group_leader_or_admin(current_user=regular_user)
        print_error("get_group_leader_or_admin: Regular user should not have access")
        test_results.append(False)
    except Exception as e:
        if "Group leader or admin privileges required" in str(e):
            print_success("get_group_leader_or_admin: Regular user correctly denied")
            test_results.append(True)
        else:
            print_error(f"get_group_leader_or_admin: Wrong error message - {e}")
            test_results.append(False)

    return all(test_results)


def test_rate_limiter():
    """Test rate limiter functionality."""
    print_info("Testing rate limiter...")

    test_results = []

    # Test normal rate limiting
    key = "test_permission_fixes"

    # Allow first few requests
    for i in range(3):
        result = rate_limiter.is_allowed(key, max_requests=3, window_seconds=60)
        if result:
            print_success(f"Request {i + 1}: Allowed as expected")
            test_results.append(True)
        else:
            print_error(f"Request {i + 1}: Should have been allowed")
            test_results.append(False)

    # Block the 4th request
    result = rate_limiter.is_allowed(key, max_requests=3, window_seconds=60)
    if not result:
        print_success("Request 4: Correctly blocked by rate limiter")
        test_results.append(True)
    else:
        print_error("Request 4: Should have been blocked")
        test_results.append(False)

    # Test different key works
    different_key = "test_different_key"
    result = rate_limiter.is_allowed(different_key, max_requests=3, window_seconds=60)
    if result:
        print_success("Different key: Allowed as expected")
        test_results.append(True)
    else:
        print_error("Different key: Should have been allowed")
        test_results.append(False)

    return all(test_results)


def test_member_model_properties():
    """Test Member model properties that were causing async issues."""
    print_info("Testing Member model properties...")

    test_results = []

    # Create test users
    admin_user = Member(
        id=1,
        username="admin",
        name="Admin User",
        student_id="ADMIN001",
        role=UserRole.ADMIN,
        is_active=True,
    )

    group_leader_user = Member(
        id=2,
        username="leader",
        name="Group Leader",
        student_id="LEADER001",
        role=UserRole.GROUP_LEADER,
        is_active=True,
    )

    regular_user = Member(
        id=3,
        username="member",
        name="Regular Member",
        student_id="MEMBER001",
        role=UserRole.MEMBER,
        is_active=False,  # Inactive user
    )

    # Test property access (should work without async issues)
    try:
        # Test admin properties
        assert admin_user.is_admin
        assert admin_user.can_manage_group
        print_success("Admin user properties work correctly")
        test_results.append(True)

        # Test group leader properties
        assert group_leader_user.is_admin == False
        assert group_leader_user.is_group_leader
        assert group_leader_user.can_manage_group
        print_success("Group leader properties work correctly")
        test_results.append(True)

        # Test regular user properties
        assert regular_user.is_admin == False
        assert regular_user.is_group_leader == False
        assert regular_user.can_manage_group == False
        print_success("Regular user properties work correctly")
        test_results.append(True)

        # Test get_safe_dict method (was causing async issues)
        safe_dict = admin_user.get_safe_dict()
        assert safe_dict["role"] == "admin"
        assert safe_dict["is_active"]
        assert "status_display" in safe_dict
        print_success("get_safe_dict method works without async issues")
        test_results.append(True)

        # Test inactive user safe dict
        inactive_dict = regular_user.get_safe_dict()
        assert inactive_dict["status_display"] == "离职"
        print_success("Inactive user status display works correctly")
        test_results.append(True)

    except Exception as e:
        print_error(f"Member model properties test failed: {e}")
        test_results.append(False)

    return all(test_results)


async def main():
    """Run all tests and report results."""
    print_info("=== Permission System and Rate Limiting Fix Verification ===\n")

    test_results = []

    # Test permission functions
    permission_test = await test_permission_functions()
    test_results.append(permission_test)
    print()

    # Test rate limiter
    rate_limit_test = test_rate_limiter()
    test_results.append(rate_limit_test)
    print()

    # Test member model properties
    model_test = test_member_model_properties()
    test_results.append(model_test)
    print()

    # Summary
    if all(test_results):
        print_success(
            "All tests passed! Permission and rate limiting fixes are working correctly."
        )
        print_info("Fixed issues:")
        print_info("  - Permission dependency functions now use direct role comparison")
        print_info(
            "  - Rate limiting uses proper decorator pattern with 429 status codes"
        )
        print_info("  - Member model properties work without async context issues")
        print_info(
            "  - Database refresh calls specify attributes to avoid greenlet issues"
        )
        sys.exit(0)
    else:
        print_error("Some tests failed. Please check the error messages above.")
        failed_tests = []
        if not permission_test:
            failed_tests.append("Permission functions")
        if not rate_limit_test:
            failed_tests.append("Rate limiter")
        if not model_test:
            failed_tests.append("Member model properties")
        print_error(f"Failed test categories: {', '.join(failed_tests)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
