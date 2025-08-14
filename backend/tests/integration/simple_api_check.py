"""
Simple API verification script
Check if new business logic APIs are properly registered
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_api_imports():
    """Check if API modules can be imported"""
    results = {"imports": {}, "total": 0, "success": 0}

    # Test imports
    import_tests = [
        ("app.main", "Main app"),
        ("app.api.v1.auth", "Auth API"),
        ("app.api.v1.members", "Members API"),
        ("app.api.v1.tasks", "Tasks API"),
        ("app.api.v1.attendance", "Attendance API"),
        ("app.api.v1.statistics", "Statistics API"),
    ]

    for module_name, description in import_tests:
        results["total"] += 1
        try:
            __import__(module_name)
            results["imports"][module_name] = {
                "status": "OK",
                "description": description,
            }
            results["success"] += 1
            print(f"[OK] {description}: {module_name}")
        except ImportError as e:
            results["imports"][module_name] = {
                "status": "FAIL",
                "description": description,
                "error": str(e),
            }
            print(f"[FAIL] {description}: {module_name} - {e}")
        except Exception as e:
            results["imports"][module_name] = {
                "status": "ERROR",
                "description": description,
                "error": str(e),
            }
            print(f"[ERROR] {description}: {module_name} - {e}")

    return results


def check_api_routes():
    """Check if API routes are registered"""
    try:
        from app.main import app

        routes_info = []
        for route in app.routes:
            if hasattr(route, "path") and hasattr(route, "methods"):
                path = route.path
                methods = list(route.methods) if route.methods else ["GET"]
                routes_info.append({"path": path, "methods": methods})

        # Check for new API paths
        new_paths = [
            "/api/v1/tasks/work-hours/recalculate",
            "/api/v1/tasks/work-hours/pending-review",
            "/api/v1/tasks/work-hours/statistics",
            "/api/v1/statistics/overview",
            "/api/v1/statistics/efficiency",
            "/api/v1/statistics/monthly-report",
            "/api/v1/statistics/export",
        ]

        found_paths = []
        for route_info in routes_info:
            for new_path in new_paths:
                if new_path in route_info["path"]:
                    found_paths.append(route_info)
                    break

        print(f"\n[ROUTES] Total routes: {len(routes_info)}")
        print(f"[ROUTES] New API paths found: {len(found_paths)}/{len(new_paths)}")

        for route in found_paths:
            print(f"  - {route['path']} [{', '.join(route['methods'])}]")

        return {
            "total_routes": len(routes_info),
            "new_paths_expected": len(new_paths),
            "new_paths_found": len(found_paths),
            "found_paths": found_paths,
        }

    except Exception as e:
        print(f"[ERROR] Routes check failed: {e}")
        return {"error": str(e)}


def check_basic_response():
    """Check basic API response"""
    try:
        from app.main import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        # Test basic endpoints
        test_endpoints = [
            "/",
            "/health",
            "/api/v1/tasks/health",
            "/api/v1/statistics/health",
        ]

        results = {}
        for endpoint in test_endpoints:
            try:
                response = client.get(endpoint)
                results[endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                }
                print(f"[API] {endpoint}: {response.status_code}")
            except Exception as e:
                results[endpoint] = {
                    "status_code": None,
                    "success": False,
                    "error": str(e),
                }
                print(f"[API] {endpoint}: ERROR - {e}")

        return results

    except Exception as e:
        print(f"[ERROR] API response check failed: {e}")
        return {"error": str(e)}


def main():
    """Main verification function"""
    print("=== Business Logic API Verification ===")
    print(f"Python: {sys.version}")
    print(f"Project root: {project_root}")

    # Check imports
    print("\n1. Checking imports...")
    import_results = check_api_imports()

    # Check routes
    print("\n2. Checking routes...")
    route_results = check_api_routes()

    # Check basic API responses
    print("\n3. Checking basic responses...")
    response_results = check_basic_response()

    # Summary
    print("\n=== Summary ===")
    import_success_rate = (import_results["success"] / import_results["total"]) * 100
    print(
        f"Import success rate: {import_success_rate:.1f}% ({import_results['success']}/{import_results['total']})"
    )

    if "error" not in route_results:
        route_success_rate = (
            route_results["new_paths_found"] / route_results["new_paths_expected"]
        ) * 100
        print(
            f"New API routes found: {route_success_rate:.1f}% ({route_results['new_paths_found']}/{route_results['new_paths_expected']})"
        )

    if "error" not in response_results:
        successful_responses = sum(
            1 for r in response_results.values() if r.get("success", False)
        )
        total_responses = len(response_results)
        response_success_rate = (
            (successful_responses / total_responses) * 100 if total_responses > 0 else 0
        )
        print(
            f"API response success rate: {response_success_rate:.1f}% ({successful_responses}/{total_responses})"
        )

    # Overall assessment
    if import_success_rate >= 80:
        print("\n[RESULT] Business Logic APIs verification: PASSED")
        return 0
    else:
        print("\n[RESULT] Business Logic APIs verification: NEEDS ATTENTION")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
