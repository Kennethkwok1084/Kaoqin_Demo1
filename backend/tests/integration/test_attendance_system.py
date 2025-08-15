"""
考勤管理系统集成测试
测试考勤记录、异常处理、统计分析等完整流程
"""

from datetime import date, datetime, timedelta

import pytest

from app.models.attendance import (
    AttendanceExceptionStatus,
)


class TestAttendanceCheckinCheckout:
    """测试签到签退功能"""

    def test_checkin_success(self, client, auth_headers_member):
        """测试成功签到"""
        checkin_data = {
            "checkin_time": datetime.now()
            .replace(hour=9, minute=0, second=0, microsecond=0)
            .isoformat(),
            "location": "办公室",
            "notes": "正常签到",
        }

        response = client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证签到响应
        assert data["success"] is True
        assert (
            "签到成功" in data["message"]
            or "checked in successfully" in data["message"]
        )
        assert "record_id" in data
        assert "checkin_time" in data
        assert data["location"] == "办公室"
        assert data["is_late"] is False  # 9点签到不算迟到
        assert data["late_minutes"] is None or data["late_minutes"] == 0

    def test_checkin_late(self, client, auth_headers_member):
        """测试迟到签到"""
        # 10点签到（假设9点上班）
        late_checkin_time = datetime.now().replace(
            hour=10, minute=30, second=0, microsecond=0
        )

        checkin_data = {
            "checkin_time": late_checkin_time.isoformat(),
            "location": "办公室",
            "notes": "迟到了",
        }

        response = client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证迟到处理
        assert data["success"] is True
        assert data["is_late"] is True
        assert data["late_minutes"] == 90  # 迟到90分钟

    def test_checkin_duplicate_same_day(self, client, auth_headers_member):
        """测试同一天重复签到"""
        checkin_data = {
            "checkin_time": datetime.now().replace(hour=8, minute=30).isoformat(),
            "location": "办公室",
        }

        # 第一次签到
        response1 = client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )
        assert response1.status_code == 200

        # 第二次签到（同一天）
        response2 = client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )

        # 应该被拒绝或更新现有记录
        assert response2.status_code in [400, 200]

        if response2.status_code == 400:
            data = response2.json()
            assert (
                "已签到" in data["message"] or "already checked in" in data["message"]
            )

    def test_checkout_success(self, client, auth_headers_member):
        """测试成功签退"""
        # 先签到
        checkin_data = {
            "checkin_time": datetime.now().replace(hour=9, minute=0).isoformat(),
            "location": "办公室",
        }
        checkin_response = client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )
        assert checkin_response.status_code == 200

        # 再签退
        checkout_data = {
            "checkout_time": datetime.now().replace(hour=18, minute=0).isoformat(),
            "location": "办公室",
            "notes": "正常下班",
        }

        response = client.post(
            "/api/attendance/checkout", json=checkout_data, headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证签退响应
        assert data["success"] is True
        assert (
            "签退成功" in data["message"]
            or "checked out successfully" in data["message"]
        )
        assert "checkout_time" in data
        assert "work_hours" in data
        assert data["work_hours"] == 9.0  # 9小时工作
        assert data["is_early_checkout"] is False

    def test_checkout_early(self, client, auth_headers_member):
        """测试早退"""
        # 先签到
        checkin_data = {
            "checkin_time": datetime.now().replace(hour=9, minute=0).isoformat(),
            "location": "办公室",
        }
        client.post(
            "/api/attendance/checkin", json=checkin_data, headers=auth_headers_member
        )

        # 早退（17点下班，16点就退了）
        early_checkout_time = datetime.now().replace(hour=16, minute=0)
        checkout_data = {
            "checkout_time": early_checkout_time.isoformat(),
            "location": "办公室",
            "notes": "有事早走",
        }

        response = client.post(
            "/api/attendance/checkout", json=checkout_data, headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证早退处理
        assert data["success"] is True
        assert data["is_early_checkout"] is True
        assert data["early_checkout_minutes"] == 60  # 早退60分钟
        assert data["work_hours"] == 7.0  # 实际工作7小时

    def test_checkout_without_checkin(self, client, auth_headers_member):
        """测试未签到就签退"""
        checkout_data = {
            "checkout_time": datetime.now().replace(hour=18, minute=0).isoformat(),
            "location": "办公室",
        }

        response = client.post(
            "/api/attendance/checkout", json=checkout_data, headers=auth_headers_member
        )

        # 应该被拒绝或自动创建签到记录
        assert response.status_code in [400, 200]

        if response.status_code == 400:
            data = response.json()
            assert "未签到" in data["message"] or "not checked in" in data["message"]


class TestAttendanceRecords:
    """测试考勤记录管理"""

    @pytest.mark.asyncio
    async def test_get_attendance_records(
        self,
        client,
        auth_headers_member,
        test_data_helper,
        test_member_user,
        db_session,
    ):
        """测试获取考勤记录"""
        # 创建一些测试考勤记录
        await test_data_helper.create_test_attendance_records(
            db_session, test_member_user.id, 7
        )

        response = client.get("/api/attendance/records", headers=auth_headers_member)

        assert response.status_code == 200
        data = response.json()

        # 验证记录列表
        assert isinstance(data, list)
        assert len(data) <= 20  # 默认分页大小

        for record in data:
            assert "id" in record
            assert "attendance_date" in record
            assert "checkin_time" in record or "checkout_time" in record
            assert "work_hours" in record
            assert "status" in record
            assert "is_late_checkin" in record
            assert "is_early_checkout" in record

    def test_get_attendance_records_with_date_filter(self, client, auth_headers_member):
        """测试按日期筛选考勤记录"""
        today = date.today()
        week_ago = today - timedelta(days=7)

        response = client.get(
            f"/api/attendance/records?date_from={week_ago}&date_to={today}",
            headers=auth_headers_member,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证日期筛选
        for record in data:
            record_date = datetime.fromisoformat(record["attendance_date"]).date()
            assert week_ago <= record_date <= today

    def test_get_attendance_record_detail(
        self, client, auth_headers_member, db_session, test_member_user
    ):
        """测试获取考勤记录详情"""
        # 先创建一个考勤记录
        from app.models.attendance import AttendanceRecord

        record = AttendanceRecord(
            member_id=test_member_user.id,
            attendance_date=date.today(),
            checkin_time=datetime.now().replace(hour=9, minute=0),
            checkout_time=datetime.now().replace(hour=18, minute=0),
            work_hours=9.0,
            status="正常",
            location="办公室",
            notes="测试记录",
            is_late_checkin=False,
            is_early_checkout=False,
        )

        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = client.get(
            f"/api/attendance/records/{record.id}", headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证详情数据
        assert data["id"] == record.id
        assert data["member_id"] == test_member_user.id
        assert data["work_hours"] == 9.0
        assert data["status"] == "正常"
        assert data["location"] == "办公室"
        assert data["notes"] == "测试记录"

    def test_update_attendance_record(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试更新考勤记录（管理员权限）"""
        # 创建考勤记录
        from app.models.attendance import AttendanceRecord

        record = AttendanceRecord(
            member_id=test_member_user.id,
            attendance_date=date.today(),
            checkin_time=datetime.now().replace(hour=9, minute=30),
            checkout_time=datetime.now().replace(hour=17, minute=30),
            work_hours=8.0,
            status="正常",
            is_late_checkin=True,
            late_checkin_minutes=30,
        )

        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        # 更新记录
        update_data = {
            "checkin_time": datetime.now().replace(hour=9, minute=0).isoformat(),
            "checkout_time": datetime.now().replace(hour=18, minute=0).isoformat(),
            "notes": "管理员修正记录",
        }

        response = client.put(
            f"/api/attendance/records/{record.id}",
            json=update_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证更新结果
        assert data["notes"] == "管理员修正记录"
        assert data["work_hours"] == 9.0  # 重新计算的工时
        assert data["is_late_checkin"] is False  # 不再迟到

    def test_delete_attendance_record(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试删除考勤记录"""
        # 创建待删除记录
        from app.models.attendance import AttendanceRecord

        record = AttendanceRecord(
            member_id=test_member_user.id,
            attendance_date=date.today() - timedelta(days=1),
            checkin_time=datetime.now(),
            work_hours=8.0,
            status="正常",
        )

        db_session.add(record)
        db_session.commit()
        db_session.refresh(record)

        response = client.delete(
            f"/api/attendance/records/{record.id}", headers=auth_headers_admin
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # 验证记录已删除
        get_response = client.get(
            f"/api/attendance/records/{record.id}", headers=auth_headers_admin
        )
        assert get_response.status_code == 404


class TestAttendanceExceptions:
    """测试考勤异常处理"""

    def test_submit_attendance_exception(self, client, auth_headers_member):
        """测试提交考勤异常申请"""
        exception_data = {
            "exception_type": "迟到",
            "exception_date": date.today().isoformat(),
            "reason": "交通堵塞导致迟到",
            "supporting_documents": "交通证明.pdf",
        }

        response = client.post(
            "/api/attendance/exceptions",
            json=exception_data,
            headers=auth_headers_member,
        )

        assert response.status_code == 201
        data = response.json()

        # 验证异常申请
        assert data["exception_type"] == "迟到"
        assert data["reason"] == "交通堵塞导致迟到"
        assert data["status"] == "pending"
        assert data["supporting_documents"] == "交通证明.pdf"
        assert "id" in data
        assert "applied_at" in data

    def test_submit_exception_future_date(self, client, auth_headers_member):
        """测试提交未来日期的异常申请"""
        future_date = date.today() + timedelta(days=1)

        exception_data = {
            "exception_type": "请假",
            "exception_date": future_date.isoformat(),
            "reason": "预约医生",
        }

        response = client.post(
            "/api/attendance/exceptions",
            json=exception_data,
            headers=auth_headers_member,
        )

        # 应该被拒绝
        assert response.status_code == 422
        error_data = response.json()
        assert "未来日期" in str(error_data) or "future date" in str(error_data)

    def test_submit_exception_too_old_date(self, client, auth_headers_member):
        """测试提交超过30天的异常申请"""
        old_date = date.today() - timedelta(days=31)

        exception_data = {
            "exception_type": "忘记打卡",
            "exception_date": old_date.isoformat(),
            "reason": "忘记打卡了",
        }

        response = client.post(
            "/api/attendance/exceptions",
            json=exception_data,
            headers=auth_headers_member,
        )

        # 应该被拒绝
        assert response.status_code == 422
        error_data = response.json()
        assert "30天" in str(error_data) or "30 days" in str(error_data)

    def test_get_attendance_exceptions(
        self, client, auth_headers_member, db_session, test_member_user
    ):
        """测试获取考勤异常列表"""
        # 创建一些异常记录
        from app.models.attendance import AttendanceException

        exceptions = []
        for i in range(3):
            exception = AttendanceException(
                member_id=test_member_user.id,
                exception_type=f"异常类型{i+1}",
                exception_date=date.today() - timedelta(days=i),
                reason=f"异常原因{i+1}",
                status=AttendanceExceptionStatus.PENDING,
                applied_at=datetime.utcnow(),
            )
            db_session.add(exception)
            exceptions.append(exception)

        db_session.commit()

        response = client.get("/api/attendance/exceptions", headers=auth_headers_member)

        assert response.status_code == 200
        data = response.json()

        # 验证异常列表
        assert isinstance(data, list)
        assert len(data) >= 3

        for exception in data:
            assert "id" in exception
            assert "exception_type" in exception
            assert "exception_date" in exception
            assert "reason" in exception
            assert "status" in exception
            assert "applied_at" in exception

    def test_get_exception_detail(
        self, client, auth_headers_member, db_session, test_member_user
    ):
        """测试获取异常详情"""
        from app.models.attendance import AttendanceException

        exception = AttendanceException(
            member_id=test_member_user.id,
            exception_type="迟到",
            exception_date=date.today(),
            reason="地铁故障",
            supporting_documents="地铁延误证明",
            status=AttendanceExceptionStatus.PENDING,
            applied_at=datetime.utcnow(),
        )

        db_session.add(exception)
        db_session.commit()
        db_session.refresh(exception)

        response = client.get(
            f"/api/attendance/exceptions/{exception.id}", headers=auth_headers_member
        )

        assert response.status_code == 200
        data = response.json()

        # 验证详情数据
        assert data["id"] == exception.id
        assert data["exception_type"] == "迟到"
        assert data["reason"] == "地铁故障"
        assert data["supporting_documents"] == "地铁延误证明"
        assert data["status"] == "pending"

    def test_approve_exception_as_admin(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试管理员批准异常申请"""
        from app.models.attendance import AttendanceException

        exception = AttendanceException(
            member_id=test_member_user.id,
            exception_type="请假",
            exception_date=date.today(),
            reason="家中有事",
            status=AttendanceExceptionStatus.PENDING,
            applied_at=datetime.utcnow(),
        )

        db_session.add(exception)
        db_session.commit()
        db_session.refresh(exception)

        # 批准申请
        approve_data = {"status": "approved", "reviewer_comments": "情况属实，批准请假"}

        response = client.patch(
            f"/api/attendance/exceptions/{exception.id}",
            json=approve_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证批准结果
        assert data["status"] == "approved"
        assert data["reviewer_comments"] == "情况属实，批准请假"
        assert "reviewer_id" in data
        assert "reviewed_at" in data

    def test_reject_exception_as_admin(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试管理员拒绝异常申请"""
        from app.models.attendance import AttendanceException

        exception = AttendanceException(
            member_id=test_member_user.id,
            exception_type="迟到",
            exception_date=date.today(),
            reason="睡过头了",
            status=AttendanceExceptionStatus.PENDING,
            applied_at=datetime.utcnow(),
        )

        db_session.add(exception)
        db_session.commit()
        db_session.refresh(exception)

        # 拒绝申请
        reject_data = {
            "status": "rejected",
            "reviewer_comments": "理由不充分，拒绝申请",
        }

        response = client.patch(
            f"/api/attendance/exceptions/{exception.id}",
            json=reject_data,
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证拒绝结果
        assert data["status"] == "rejected"
        assert data["reviewer_comments"] == "理由不充分，拒绝申请"

    def test_process_exception_as_non_admin(
        self, client, auth_headers_member, db_session, test_admin_user
    ):
        """测试非管理员处理异常申请"""
        from app.models.attendance import AttendanceException

        exception = AttendanceException(
            member_id=test_admin_user.id,
            exception_type="请假",
            exception_date=date.today(),
            reason="私事",
            status=AttendanceExceptionStatus.PENDING,
            applied_at=datetime.utcnow(),
        )

        db_session.add(exception)
        db_session.commit()
        db_session.refresh(exception)

        approve_data = {"status": "approved", "reviewer_comments": "不应该被批准"}

        response = client.patch(
            f"/api/attendance/exceptions/{exception.id}",
            json=approve_data,
            headers=auth_headers_member,
        )

        # 应该被拒绝
        assert response.status_code == 403


class TestAttendanceStatistics:
    """测试考勤统计"""

    @pytest.mark.asyncio
    async def test_get_monthly_summary(
        self,
        client,
        auth_headers_member,
        test_data_helper,
        test_member_user,
        db_session,
    ):
        """测试获取月度考勤汇总"""
        # 创建本月考勤记录
        await test_data_helper.create_test_attendance_records(
            db_session, test_member_user.id, 20
        )

        today = date.today()
        response = client.get(
            f"/api/attendance/summary/{today.year}/{today.month}",
            headers=auth_headers_member,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证月度汇总
        assert data["member_id"] == test_member_user.id
        assert data["year"] == today.year
        assert data["month"] == today.month
        assert "total_work_days" in data
        assert "expected_work_days" in data
        assert "attendance_rate" in data
        assert "total_work_hours" in data
        assert "average_work_hours" in data
        assert "total_late_days" in data
        assert "total_early_days" in data
        assert "exception_summary" in data
        assert "records" in data

        # 验证数据合理性
        assert data["attendance_rate"] >= 0 and data["attendance_rate"] <= 100
        assert data["total_work_hours"] >= 0
        assert data["total_late_days"] >= 0

    @pytest.mark.asyncio
    async def test_get_attendance_statistics(
        self, client, auth_headers_admin, test_data_helper, test_member_user, db_session
    ):
        """测试获取考勤统计"""
        # 创建测试数据
        await test_data_helper.create_test_attendance_records(
            db_session, test_member_user.id, 15
        )

        today = date.today()
        week_ago = today - timedelta(days=7)

        response = client.get(
            f"/api/attendance/statistics?date_from={week_ago}&date_to={today}",
            headers=auth_headers_admin,
        )

        assert response.status_code == 200
        data = response.json()

        # 验证统计数据
        assert "date_from" in data
        assert "date_to" in data
        assert "total_records" in data
        assert "total_members" in data
        assert "total_work_hours" in data
        assert "average_work_hours" in data
        assert "late_rate" in data
        assert "early_checkout_rate" in data
        assert "department_statistics" in data
        assert "exception_statistics" in data

        # 验证数据合理性
        assert data["total_records"] >= 0
        assert data["total_members"] >= 1
        assert data["late_rate"] >= 0 and data["late_rate"] <= 100
        assert data["early_checkout_rate"] >= 0 and data["early_checkout_rate"] <= 100

    def test_export_attendance_data(self, client, auth_headers_admin):
        """测试导出考勤数据"""
        today = date.today()
        week_ago = today - timedelta(days=7)

        export_data = {
            "date_from": week_ago.isoformat(),
            "date_to": today.isoformat(),
            "format": "excel",
            "include_summary": True,
        }

        response = client.post(
            "/api/attendance/export", json=export_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证导出响应
            assert data["success"] is True
            assert "download_url" in data
            assert "filename" in data
            assert "total_records" in data
            assert "expires_at" in data

            # 验证文件信息
            assert data["filename"].endswith(".xlsx") or data["filename"].endswith(
                ".csv"
            )
            assert data["total_records"] >= 0
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]


class TestAttendanceBulkOperations:
    """测试考勤批量操作"""

    def test_bulk_import_attendance(
        self, client, auth_headers_admin, test_member_user, test_group_leader
    ):
        """测试批量导入考勤记录"""
        import_data = {
            "records": [
                {
                    "member_id": test_member_user.id,
                    "attendance_date": date.today().isoformat(),
                    "checkin_time": datetime.now()
                    .replace(hour=9, minute=0)
                    .isoformat(),
                    "checkout_time": datetime.now()
                    .replace(hour=18, minute=0)
                    .isoformat(),
                    "location": "办公室",
                    "notes": "批量导入记录1",
                },
                {
                    "member_id": test_group_leader.id,
                    "attendance_date": date.today().isoformat(),
                    "checkin_time": datetime.now()
                    .replace(hour=8, minute=30)
                    .isoformat(),
                    "checkout_time": datetime.now()
                    .replace(hour=17, minute=30)
                    .isoformat(),
                    "location": "办公室",
                    "notes": "批量导入记录2",
                },
            ]
        }

        response = client.post(
            "/api/attendance/bulk-import", json=import_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证批量导入结果
            assert data["success"] is True
            assert data["total_records"] == 2
            assert data["successful_records"] >= 0
            assert data["failed_records"] >= 0
            assert (
                data["successful_records"] + data["failed_records"]
                == data["total_records"]
            )
            assert "errors" in data
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]

    def test_bulk_update_attendance_status(
        self, client, auth_headers_admin, db_session, test_member_user
    ):
        """测试批量更新考勤状态"""
        # 创建一些考勤记录
        from app.models.attendance import AttendanceRecord

        records = []
        for i in range(3):
            record = AttendanceRecord(
                member_id=test_member_user.id,
                attendance_date=date.today() - timedelta(days=i),
                checkin_time=datetime.now().replace(hour=9),
                checkout_time=datetime.now().replace(hour=18),
                work_hours=9.0,
                status="待审核",
            )
            db_session.add(record)
            records.append(record)

        db_session.commit()
        for record in records:
            db_session.refresh(record)

        # 批量更新状态
        update_data = {
            "record_ids": [record.id for record in records],
            "status": "已确认",
            "reason": "批量确认考勤记录",
        }

        response = client.patch(
            "/api/attendance/bulk-update", json=update_data, headers=auth_headers_admin
        )

        if response.status_code == 200:
            data = response.json()

            # 验证批量更新结果
            assert data["success"] is True
            assert data["updated_count"] == 3
        else:
            # 如果功能未实现
            assert response.status_code in [404, 405, 501]


class TestAttendanceIntegration:
    """测试考勤系统集成"""

    def test_full_attendance_workflow(
        self, client, auth_headers_member, auth_headers_admin
    ):
        """测试完整考勤流程"""
        # 1. 签到
        checkin_response = client.post(
            "/api/attendance/checkin",
            json={"location": "办公室"},
            headers=auth_headers_member,
        )
        assert checkin_response.status_code == 200

        # 2. 签退
        checkout_response = client.post(
            "/api/attendance/checkout",
            json={"location": "办公室"},
            headers=auth_headers_member,
        )
        assert checkout_response.status_code == 200

        # 3. 查看记录
        records_response = client.get(
            "/api/attendance/records", headers=auth_headers_member
        )
        assert records_response.status_code == 200

        # 4. 提交异常申请
        exception_response = client.post(
            "/api/attendance/exceptions",
            json={
                "exception_type": "备注",
                "exception_date": date.today().isoformat(),
                "reason": "补充说明今日工作内容",
            },
            headers=auth_headers_member,
        )
        assert exception_response.status_code == 201
        exception_id = exception_response.json()["id"]

        # 5. 管理员处理异常
        approve_response = client.patch(
            f"/api/attendance/exceptions/{exception_id}",
            json={"status": "approved", "reviewer_comments": "已确认"},
            headers=auth_headers_admin,
        )
        assert approve_response.status_code == 200

        # 6. 查看月度汇总
        today = date.today()
        summary_response = client.get(
            f"/api/attendance/summary/{today.year}/{today.month}",
            headers=auth_headers_member,
        )
        assert summary_response.status_code == 200

        # 验证完整流程数据一致性
        summary_data = summary_response.json()
        assert summary_data["total_work_days"] >= 1
        assert summary_data["total_work_hours"] >= 0
