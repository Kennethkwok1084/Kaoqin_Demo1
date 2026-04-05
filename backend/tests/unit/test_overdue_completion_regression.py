from datetime import datetime, timedelta

from app.models.task import RepairTask


def test_completed_task_late_completion_is_overdue():
    response_time = datetime.utcnow() - timedelta(hours=60)
    completion_time = response_time + timedelta(hours=55)

    task = RepairTask(
        task_id="TEST_LATE_COMPLETION_001",
        title="已完成但超时的维修单",
        member_id=1,
        report_time=response_time - timedelta(hours=1),
        response_time=response_time,
        completion_time=completion_time,
    )

    assert task.is_overdue_completion is True


def test_completed_task_within_threshold_is_not_overdue():
    response_time = datetime.utcnow() - timedelta(hours=20)
    completion_time = response_time + timedelta(hours=12)

    task = RepairTask(
        task_id="TEST_ON_TIME_COMPLETION_001",
        title="已完成且未超时的维修单",
        member_id=1,
        report_time=response_time - timedelta(hours=1),
        response_time=response_time,
        completion_time=completion_time,
    )

    assert task.is_overdue_completion is False
