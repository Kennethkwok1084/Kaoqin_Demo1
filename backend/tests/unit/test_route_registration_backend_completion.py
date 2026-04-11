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


def test_coop_workflow_routes_registered() -> None:
    assert _has_route("/api/v1/tasks/{task_id}/signup", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/signups", "GET")
    assert _has_route("/api/v1/admin/tasks/{task_id}/signups/{signup_id}/review", "POST")
    assert _has_route("/api/v1/tasks/{task_id}/sign/repair/request", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/qrcode/generate", "POST")


def test_inspection_sampling_workflow_routes_registered() -> None:
    assert _has_route("/api/v1/admin/tasks/{task_id}/inspection-points", "POST")
    assert _has_route("/api/v1/tasks/{task_id}/inspection-points", "GET")
    assert _has_route("/api/v1/tasks/{task_id}/inspection-records", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/sampling/generate-targets", "POST")
    assert _has_route("/api/v1/network-tests/{record_id}/submit", "POST")


def test_task_lifecycle_routes_registered() -> None:
    assert _has_route("/api/v1/tasks", "GET")
    assert _has_route("/api/v1/tasks/{task_id}", "GET")
    assert _has_route("/api/v1/admin/tasks", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}", "PUT")
    assert _has_route("/api/v1/admin/tasks/{task_id}/publish", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/close", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/assign", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/slots", "POST")
    assert _has_route("/api/v1/tasks/{task_id}/slots", "GET")
    assert _has_route("/api/v1/tasks/{task_id}/sign-in", "POST")
    assert _has_route("/api/v1/tasks/{task_id}/sign-out", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/sign-records", "GET")
    assert _has_route("/api/v1/admin/sign-records/{record_id}/approve", "POST")
    assert _has_route("/api/v1/admin/tasks/{task_id}/no-show", "POST")


def test_repair_order_and_media_routes_registered() -> None:
    assert _has_route("/api/v1/repair-orders", "POST")
    assert _has_route("/api/v1/repair-orders/{ticket_id}", "PUT")
    assert _has_route("/api/v1/repair-orders/{ticket_id}/participants", "POST")
    assert _has_route("/api/v1/repair-orders/{ticket_id}/ocr", "POST")
    assert _has_route("/api/v1/repair-orders/{ticket_id}/ocr/correct", "POST")
    assert _has_route("/api/v1/repair-orders/{ticket_id}/match-candidates", "GET")
    assert _has_route("/api/v1/repair-orders/{ticket_id}/match", "POST")
    assert _has_route("/api/v1/admin/repair-orders/{ticket_id}/approve-match", "POST")
    assert _has_route("/api/v1/admin/repair-imports", "POST")
    assert _has_route("/api/v1/media/upload-image", "POST")
    assert _has_route("/api/v1/media/upload-video", "POST")
    assert _has_route("/api/v1/media/{media_id}", "GET")


def test_user_and_profile_routes_registered() -> None:
    assert _has_route("/api/v1/admin/users", "GET")
    assert _has_route("/api/v1/admin/users", "POST")
    assert _has_route("/api/v1/admin/users/{user_id}/status", "PUT")
    assert _has_route("/api/v1/users/profile", "PUT")


def test_config_workhour_and_todo_routes_registered() -> None:
    assert _has_route("/api/v1/admin/configs", "GET")
    assert _has_route("/api/v1/admin/configs", "PUT")
    assert _has_route("/api/v1/admin/workhour-rules", "GET")
    assert _has_route("/api/v1/admin/workhour-rules", "POST")
    assert _has_route("/api/v1/admin/workhour-rules/{rule_id}", "PUT")
    assert _has_route("/api/v1/workhours/my", "GET")
    assert _has_route("/api/v1/admin/workhours", "GET")
    assert _has_route("/api/v1/admin/workhours/{entry_id}/approve", "POST")
    assert _has_route("/api/v1/admin/workhours/{entry_id}/reject", "POST")
    assert _has_route("/api/v1/admin/workhours/manual", "POST")
    assert _has_route("/api/v1/admin/todos", "GET")
    assert _has_route("/api/v1/admin/todos/{todo_id}/claim", "POST")
    assert _has_route("/api/v1/admin/todos/{todo_id}/finish", "POST")
    assert _has_route("/api/v1/internal/workhours/recalculate", "POST")


def test_campus_and_ops_stats_routes_registered() -> None:
    assert _has_route("/api/v1/buildings", "GET")
    assert _has_route("/api/v1/buildings/{building_id}/rooms", "GET")
    assert _has_route("/api/v1/admin/rooms/import", "POST")
    assert _has_route("/api/v1/admin/rooms/{room_id}/wifi-profile", "PUT")
    assert _has_route("/api/v1/admin/stats/workhours", "GET")
    assert _has_route("/api/v1/admin/stats/repair-problems", "GET")
    assert _has_route("/api/v1/admin/stats/rankings", "GET")
    assert _has_route("/api/v1/admin/stats/network-quality", "GET")
