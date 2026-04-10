"""回归测试：验证本轮 backend 补全路由已注册。"""

from app.main import app


def _has_route(path: str, method: str) -> bool:
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", None) == path and method in (route.methods or set()):
            return True
    return False


def test_attendance_completion_routes_registered() -> None:
    assert _has_route("/api/v1/attendance/check-in", "POST")
    assert _has_route("/api/v1/attendance/check-out", "POST")
    assert _has_route("/api/v1/attendance/summary/{month}", "GET")


def test_existing_bulk_routes_still_registered() -> None:
    assert _has_route("/api/v1/tasks/rush-marking/batch", "POST")
    assert _has_route("/api/v1/tasks/work-hours/bulk-recalculate", "POST")
