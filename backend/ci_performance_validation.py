"""
CI/CD Performance Validation Script
Tests all database optimizations and generates a performance report.
"""

import asyncio
import os
import time
import sys
from typing import Dict, Any

# Set testing environment for demonstration
os.environ["TESTING"] = "true"
os.environ["CI"] = "true"


async def validate_optimizations() -> Dict[str, Any]:
    """Validate all CI/CD optimizations."""
    from app.core.database import (
        get_environment_info, 
        get_pool_status, 
        check_database_health,
        DatabaseTransaction,
        AsyncSessionLocal
    )
    
    results = {}
    
    # Test 1: Environment Detection
    print("=== Testing Environment Detection ===")
    env_info = get_environment_info()
    results["environment"] = env_info
    print(f"CI Environment: {env_info['is_ci']}")
    print(f"Testing Environment: {env_info['is_testing']}")
    print(f"Pool Config: {env_info['pool_config']}")
    
    # Test 2: Pool Status
    print("\n=== Testing Connection Pool Status ===")
    pool_status = await get_pool_status()
    results["pool_status"] = pool_status
    print(f"Environment Type: {pool_status.get('environment', 'unknown')}")
    print(f"Pool Size: {pool_status.get('pool_size', 0)}")
    
    # Test 3: Health Check Performance
    print("\n=== Testing Database Health Check Performance ===")
    health_times = []
    for timeout in [1, 2, 5]:
        start = time.time()
        health = await check_database_health(timeout_seconds=timeout)
        duration = time.time() - start
        health_times.append({"timeout": timeout, "duration": duration, "success": health})
        print(f"Health check ({timeout}s timeout): {health} in {duration:.3f}s")
    
    results["health_checks"] = health_times
    
    # Test 4: Session Management Performance
    print("\n=== Testing Session Management Performance ===")
    session_times = []
    
    for i in range(3):  # Test 3 sessions
        start = time.time()
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
        except Exception as e:
            print(f"Session {i+1} error: {e}")
            continue
        
        duration = time.time() - start
        session_times.append(duration)
        print(f"Session {i+1}: {duration:.3f}s")
    
    results["session_performance"] = {
        "average": sum(session_times) / len(session_times) if session_times else 0,
        "max": max(session_times) if session_times else 0,
        "min": min(session_times) if session_times else 0,
        "times": session_times
    }
    
    # Test 5: Transaction Timeout Behavior
    print("\n=== Testing Transaction Timeout Behavior ===")
    try:
        async with AsyncSessionLocal() as session:
            # Test with CI environment timeout (should be 10 seconds)
            async with DatabaseTransaction(session, timeout_seconds=1):
                from sqlalchemy import text
                await session.execute(text("SELECT 1"))
        
        results["transaction_timeout"] = "success"
        print("Transaction timeout test: SUCCESS")
    except Exception as e:
        results["transaction_timeout"] = f"error: {e}"
        print(f"Transaction timeout test: {e}")
    
    return results


async def generate_performance_report():
    """Generate comprehensive performance report."""
    print("🚀 Starting CI/CD Database Performance Validation")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        results = await validate_optimizations()
        total_time = time.time() - start_time
        
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE REPORT SUMMARY")
        print("=" * 60)
        
        # Environment Summary
        env = results["environment"]
        print(f"Environment: {'CI' if env['is_ci'] else 'Local'}")
        print(f"Pool Size: {env['pool_config']['pool_size']}")
        print(f"Pool Timeout: {env['pool_config']['pool_timeout']}s")
        print(f"Pool Recycle: {env['pool_config']['pool_recycle']}s")
        
        # Performance Summary
        health_avg = sum(h["duration"] for h in results["health_checks"]) / len(results["health_checks"])
        session_perf = results["session_performance"]
        
        print(f"\nPerformance Metrics:")
        print(f"  Average Health Check: {health_avg:.3f}s")
        print(f"  Average Session Time: {session_perf['average']:.3f}s")
        print(f"  Transaction Timeout: {results['transaction_timeout']}")
        print(f"  Total Validation Time: {total_time:.3f}s")
        
        # Success Criteria
        success_criteria = [
            ("Health checks < 1s", health_avg < 1.0),
            ("Session creation < 0.5s", session_perf['average'] < 0.5),
            ("No transaction errors", "success" in results['transaction_timeout']),
            ("Total validation < 10s", total_time < 10.0),
        ]
        
        print(f"\n✅ Success Criteria:")
        all_passed = True
        for criteria, passed in success_criteria:
            status = "PASS" if passed else "FAIL"
            print(f"  {criteria}: {status}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL OPTIMIZATIONS WORKING CORRECTLY!")
            return 0
        else:
            print("⚠️  SOME OPTIMIZATIONS NEED ATTENTION")
            return 1
            
    except Exception as e:
        print(f"\n❌ VALIDATION FAILED: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(generate_performance_report())
    sys.exit(exit_code)
