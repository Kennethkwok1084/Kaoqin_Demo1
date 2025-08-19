"""Initial tables creation for complete attendance system

Revision ID: 20250750_0000
Revises: None
Create Date: 2025-08-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20250750_0000"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create complete initial tables for attendance system."""

    # Create all required enums first (PostgreSQL compatible syntax with proper exception handling)
    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE userrole AS ENUM ('admin', 'group_leader', 'member', 'guest');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE taskstatus AS ENUM ('pending', 'in_progress', 'completed', 'cancelled', 'on_hold');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE taskcategory AS ENUM ('network_repair', 'hardware_repair', 'software_support', 'monitoring', 'assistance', 'other');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE taskpriority AS ENUM ('low', 'medium', 'high', 'urgent');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE tasktype AS ENUM ('online', 'offline');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE tasktagtype AS ENUM ('rush_order', 'non_default_rating', 'timeout_response', 'timeout_processing', 'bad_rating', 'bonus', 'penalty', 'category');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    op.execute(
        """
        DO $$ 
        BEGIN
            CREATE TYPE attendanceexceptionstatus AS ENUM ('pending', 'approved', 'rejected');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """
    )

    # Create members table first (referenced by other tables)
    op.create_table(
        "members",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "username",
            sa.String(length=50),
            nullable=False,
            comment="登录用户名（不含特殊字符和中文，可修改）",
        ),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="真实姓名（可含中文和·符号）",
        ),
        sa.Column(
            "student_id",
            sa.String(length=20),
            nullable=True,
            comment="学号/员工号（纯数字，可选）",
        ),
        sa.Column(
            "phone",
            sa.String(length=11),
            nullable=True,
            comment="手机号（纯数字，可选）",
        ),
        sa.Column(
            "email", sa.String(length=100), nullable=True, comment="邮箱地址（可选）"
        ),
        sa.Column(
            "department",
            sa.String(length=100),
            nullable=False,
            server_default="信息化建设处",
            comment="部门（默认信息化建设处）",
        ),
        sa.Column(
            "class_name", sa.String(length=50), nullable=False, comment="班级（必填）"
        ),
        sa.Column("group_id", sa.Integer(), nullable=True, comment="小组ID（可选）"),
        sa.Column(
            "join_date", sa.Date(), nullable=False, comment="入职日期（默认导入时间）"
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
            comment="密码哈希（初始密码123456）",
        ),
        sa.Column(
            "role",
            sa.Enum(
                "admin",
                "group_leader",
                "member",
                "guest",
                name="userrole",
                create_type=False,
            ),
            nullable=False,
            server_default="member",
            comment="用户角色",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="在职状态（True=在职，False=离职）",
        ),
        sa.Column(
            "profile_completed",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="是否已完善个人信息（首次登录需要完善）",
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="邮箱验证状态",
        ),
        sa.Column("last_login", sa.DateTime(), nullable=True, comment="最后登录时间"),
        sa.Column(
            "login_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="登录次数",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_member_username"),
        sa.UniqueConstraint("student_id", name="uq_member_student_id"),
        comment="成员信息表（重构版）",
    )
    op.create_index(op.f("ix_members_id"), "members", ["id"], unique=False)
    op.create_index(op.f("ix_members_username"), "members", ["username"], unique=False)
    op.create_index(op.f("ix_members_name"), "members", ["name"], unique=False)
    op.create_index(
        op.f("ix_members_student_id"), "members", ["student_id"], unique=False
    )

    # Create task_tags table
    op.create_table(
        "task_tags",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column("name", sa.String(length=50), nullable=False, comment="Tag name"),
        sa.Column("description", sa.Text(), nullable=True, comment="Tag description"),
        sa.Column(
            "work_minutes_modifier",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Work minutes modifier (+/- minutes)",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="Whether the tag is active",
        ),
        sa.Column(
            "tag_type",
            sa.Enum(
                "rush_order",
                "non_default_rating",
                "timeout_response",
                "timeout_processing",
                "bad_rating",
                "bonus",
                "penalty",
                "category",
                name="tasktagtype",
            ),
            nullable=False,
            server_default="category",
            comment="Tag type for categorization and work hour calculation",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        comment="Task tags table",
    )
    op.create_index(op.f("ix_task_tags_id"), "task_tags", ["id"], unique=False)
    op.create_index(op.f("ix_task_tags_name"), "task_tags", ["name"], unique=True)

    # Create repair_tasks table
    op.create_table(
        "repair_tasks",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "task_id",
            sa.String(length=50),
            nullable=False,
            comment="External task ID from work order system",
        ),
        sa.Column(
            "member_id", sa.Integer(), nullable=False, comment="Assigned member ID"
        ),
        sa.Column("title", sa.String(length=200), nullable=False, comment="Task title"),
        sa.Column(
            "description", sa.Text(), nullable=True, comment="Detailed task description"
        ),
        sa.Column(
            "location", sa.String(length=200), nullable=True, comment="Task location"
        ),
        sa.Column(
            "category",
            sa.Enum(
                "network_repair",
                "hardware_repair",
                "software_support",
                "monitoring",
                "assistance",
                "other",
                name="taskcategory",
            ),
            nullable=False,
            server_default="network_repair",
            comment="Task category",
        ),
        sa.Column(
            "priority",
            sa.Enum(
                "low",
                "medium",
                "high",
                "urgent",
                name="taskpriority",
                create_type=False,
            ),
            nullable=False,
            server_default="medium",
            comment="Task priority",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "cancelled",
                "on_hold",
                name="taskstatus",
            ),
            nullable=False,
            server_default="pending",
            comment="Task status",
        ),
        sa.Column(
            "task_type",
            sa.Enum("online", "offline", name="tasktype", create_type=False),
            nullable=False,
            server_default="online",
            comment="Task type (online/offline)",
        ),
        sa.Column(
            "report_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Task report time",
        ),
        sa.Column(
            "response_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Task response time",
        ),
        sa.Column(
            "completion_time",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Task completion time",
        ),
        sa.Column(
            "due_date",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Task due date (usually equals completion_time from import data)",
        ),
        sa.Column("feedback", sa.Text(), nullable=True, comment="User feedback"),
        sa.Column(
            "rating", sa.Integer(), nullable=True, comment="User rating (1-5 stars)"
        ),
        sa.Column(
            "reporter_name",
            sa.String(length=50),
            nullable=True,
            comment="Reporter name",
        ),
        sa.Column(
            "reporter_contact",
            sa.String(length=100),
            nullable=True,
            comment="Reporter contact information",
        ),
        sa.Column(
            "work_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Calculated work minutes",
        ),
        sa.Column(
            "base_work_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
            comment="Base work minutes before modifiers",
        ),
        sa.Column(
            "import_batch_id",
            sa.String(length=50),
            nullable=True,
            comment="Import batch ID for tracking",
        ),
        sa.Column(
            "is_matched",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="Whether task was matched during import",
        ),
        sa.Column(
            "original_data", sa.JSON(), nullable=True, comment="A表原始数据完整保存"
        ),
        sa.Column(
            "matched_member_data", sa.JSON(), nullable=True, comment="B表匹配的成员数据"
        ),
        sa.Column(
            "is_rush_order",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="爆单标记，独立计算工时",
        ),
        sa.Column(
            "work_order_status",
            sa.String(length=50),
            nullable=True,
            comment="A表工单状态（用于状态映射）",
        ),
        sa.Column(
            "repair_form",
            sa.String(length=50),
            nullable=True,
            comment="B表检修形式（用于线上/线下判断）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("task_id", name="uq_repair_task_task_id"),
        comment="Repair tasks table",
    )
    op.create_index(op.f("ix_repair_tasks_id"), "repair_tasks", ["id"], unique=False)
    op.create_index(
        op.f("ix_repair_tasks_task_id"), "repair_tasks", ["task_id"], unique=True
    )
    op.create_index(
        op.f("ix_repair_tasks_member_id"), "repair_tasks", ["member_id"], unique=False
    )
    op.create_index(
        op.f("ix_repair_tasks_status"), "repair_tasks", ["status"], unique=False
    )
    op.create_index(
        "idx_repair_task_report_time", "repair_tasks", ["report_time"], unique=False
    )
    op.create_index(
        "idx_repair_task_member_status",
        "repair_tasks",
        ["member_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_repair_task_import_batch",
        "repair_tasks",
        ["import_batch_id"],
        unique=False,
    )

    # Create monitoring_tasks table
    op.create_table(
        "monitoring_tasks",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "member_id", sa.Integer(), nullable=False, comment="Assigned member ID"
        ),
        sa.Column("title", sa.String(length=200), nullable=False, comment="Task title"),
        sa.Column("description", sa.Text(), nullable=True, comment="Task description"),
        sa.Column(
            "location",
            sa.String(length=200),
            nullable=True,
            comment="Monitoring location",
        ),
        sa.Column(
            "monitoring_type",
            sa.String(length=50),
            nullable=False,
            comment="Monitoring type (inspection, maintenance, etc.)",
        ),
        sa.Column(
            "start_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Task start time",
        ),
        sa.Column(
            "end_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Task end time",
        ),
        sa.Column(
            "work_minutes", sa.Integer(), nullable=False, comment="Actual work minutes"
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "cancelled",
                "on_hold",
                name="taskstatus",
            ),
            nullable=False,
            server_default="completed",
            comment="Task status",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Monitoring tasks table",
    )
    op.create_index(
        op.f("ix_monitoring_tasks_id"), "monitoring_tasks", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_monitoring_tasks_member_id"),
        "monitoring_tasks",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        "idx_monitoring_task_member_time",
        "monitoring_tasks",
        ["member_id", "start_time"],
        unique=False,
    )

    # Create assistance_tasks table
    op.create_table(
        "assistance_tasks",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "member_id", sa.Integer(), nullable=False, comment="Assisting member ID"
        ),
        sa.Column(
            "title",
            sa.String(length=200),
            nullable=False,
            comment="Assistance task title",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="Task description"),
        sa.Column(
            "assisted_department",
            sa.String(length=100),
            nullable=True,
            comment="Assisted department/team",
        ),
        sa.Column(
            "assisted_person",
            sa.String(length=50),
            nullable=True,
            comment="Assisted person name",
        ),
        sa.Column(
            "start_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Task start time",
        ),
        sa.Column(
            "end_time",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Task end time",
        ),
        sa.Column(
            "work_minutes",
            sa.Integer(),
            nullable=False,
            comment="Assistance work minutes",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "in_progress",
                "completed",
                "cancelled",
                "on_hold",
                name="taskstatus",
            ),
            nullable=False,
            server_default="completed",
            comment="Task status",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Assistance tasks table",
    )
    op.create_index(
        op.f("ix_assistance_tasks_id"), "assistance_tasks", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_assistance_tasks_member_id"),
        "assistance_tasks",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        "idx_assistance_task_member_time",
        "assistance_tasks",
        ["member_id", "start_time"],
        unique=False,
    )

    # Create task_tag_associations table (many-to-many for repair_tasks and task_tags)
    op.create_table(
        "task_tag_associations",
        sa.Column("task_id", sa.Integer(), nullable=False, comment="Task ID"),
        sa.Column("tag_id", sa.Integer(), nullable=False, comment="Tag ID"),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["repair_tasks.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["task_tags.id"],
        ),
        sa.PrimaryKeyConstraint("task_id", "tag_id"),
        comment="Association table for tasks and tags",
    )

    # Create attendance_records table (daily attendance)
    op.create_table(
        "attendance_records",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column("member_id", sa.Integer(), nullable=False, comment="Member ID"),
        sa.Column(
            "attendance_date", sa.Date(), nullable=False, comment="Attendance date"
        ),
        sa.Column(
            "checkin_time", sa.DateTime(), nullable=True, comment="Check-in time"
        ),
        sa.Column(
            "checkout_time", sa.DateTime(), nullable=True, comment="Check-out time"
        ),
        sa.Column(
            "work_hours", sa.Float(), server_default="0.0", comment="Total work hours"
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default="未签到",
            comment="Attendance status",
        ),
        sa.Column(
            "location",
            sa.String(length=200),
            nullable=True,
            comment="Check-in/out location",
        ),
        sa.Column("notes", sa.Text(), nullable=True, comment="Attendance notes"),
        sa.Column(
            "is_late_checkin",
            sa.Boolean(),
            server_default="false",
            comment="Whether check-in was late",
        ),
        sa.Column(
            "late_checkin_minutes",
            sa.Integer(),
            nullable=True,
            comment="Minutes late for check-in",
        ),
        sa.Column(
            "is_early_checkout",
            sa.Boolean(),
            server_default="false",
            comment="Whether checkout was early",
        ),
        sa.Column(
            "early_checkout_minutes",
            sa.Integer(),
            nullable=True,
            comment="Minutes early for checkout",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "member_id", "attendance_date", name="uq_attendance_member_date"
        ),
        comment="Daily attendance records table",
    )
    op.create_index(
        op.f("ix_attendance_records_id"), "attendance_records", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_attendance_records_member_id"),
        "attendance_records",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_records_attendance_date"),
        "attendance_records",
        ["attendance_date"],
        unique=False,
    )
    op.create_index(
        "idx_attendance_date_member",
        "attendance_records",
        ["attendance_date", "member_id"],
        unique=False,
    )

    # Create attendance_exceptions table
    op.create_table(
        "attendance_exceptions",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column(
            "member_id",
            sa.Integer(),
            nullable=False,
            comment="Member ID who made the request",
        ),
        sa.Column(
            "exception_type",
            sa.String(length=50),
            nullable=False,
            comment="Type of exception (迟到/早退/忘记打卡/请假等)",
        ),
        sa.Column(
            "exception_date", sa.Date(), nullable=False, comment="Date of the exception"
        ),
        sa.Column(
            "reason", sa.Text(), nullable=False, comment="Reason for the exception"
        ),
        sa.Column(
            "supporting_documents",
            sa.Text(),
            nullable=True,
            comment="Supporting documents or evidence",
        ),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "approved", "rejected", name="attendanceexceptionstatus"
            ),
            nullable=False,
            server_default="pending",
            comment="Processing status",
        ),
        sa.Column(
            "applied_at",
            sa.DateTime(),
            nullable=False,
            comment="When the request was submitted",
        ),
        sa.Column(
            "reviewer_id",
            sa.Integer(),
            nullable=True,
            comment="ID of the reviewer (admin)",
        ),
        sa.Column(
            "reviewer_comments",
            sa.Text(),
            nullable=True,
            comment="Comments from the reviewer",
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(),
            nullable=True,
            comment="When the request was reviewed",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        comment="Attendance exception requests table",
    )
    op.create_index(
        op.f("ix_attendance_exceptions_id"),
        "attendance_exceptions",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_exceptions_member_id"),
        "attendance_exceptions",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_exceptions_exception_date"),
        "attendance_exceptions",
        ["exception_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_attendance_exceptions_status"),
        "attendance_exceptions",
        ["status"],
        unique=False,
    )
    op.create_index(
        "idx_exception_member_date",
        "attendance_exceptions",
        ["member_id", "exception_date"],
        unique=False,
    )
    op.create_index(
        "idx_exception_status_date",
        "attendance_exceptions",
        ["status", "applied_at"],
        unique=False,
    )

    # Create monthly_attendance_summaries table
    op.create_table(
        "monthly_attendance_summaries",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
            comment="Primary key",
        ),
        sa.Column("member_id", sa.Integer(), nullable=False, comment="Member ID"),
        sa.Column("year", sa.Integer(), nullable=False, comment="Year"),
        sa.Column("month", sa.Integer(), nullable=False, comment="Month (1-12)"),
        sa.Column(
            "repair_task_hours",
            sa.Float(),
            server_default="0.0",
            comment="本月报修任务累计时长（小时）",
        ),
        sa.Column(
            "monitoring_hours",
            sa.Float(),
            server_default="0.0",
            comment="本月监控任务累计时长（小时）",
        ),
        sa.Column(
            "assistance_hours",
            sa.Float(),
            server_default="0.0",
            comment="本月协助任务累计时长（小时）",
        ),
        sa.Column(
            "carried_hours",
            sa.Float(),
            server_default="0.0",
            comment="上月结转的剩余时长（小时）",
        ),
        sa.Column(
            "total_hours",
            sa.Float(),
            server_default="0.0",
            comment="实际总工时（小时）",
        ),
        sa.Column(
            "remaining_hours",
            sa.Float(),
            server_default="0.0",
            comment="扣除后可结转至下月的剩余工时",
        ),
        sa.Column(
            "online_repair_hours",
            sa.Float(),
            server_default="0.0",
            comment="线上报修任务时长（40分钟/单）",
        ),
        sa.Column(
            "offline_repair_hours",
            sa.Float(),
            server_default="0.0",
            comment="线下报修任务时长（100分钟/单）",
        ),
        sa.Column(
            "rush_task_hours",
            sa.Float(),
            server_default="0.0",
            comment="爆单任务额外时长（15分钟/单）",
        ),
        sa.Column(
            "positive_review_hours",
            sa.Float(),
            server_default="0.0",
            comment="非默认好评额外时长（30分钟/单）",
        ),
        sa.Column(
            "penalty_hours",
            sa.Float(),
            server_default="0.0",
            comment="异常扣时总计（小时）",
        ),
        sa.Column(
            "late_response_penalty_hours",
            sa.Float(),
            server_default="0.0",
            comment="超时响应扣时（30分钟/单/人）",
        ),
        sa.Column(
            "late_completion_penalty_hours",
            sa.Float(),
            server_default="0.0",
            comment="超时处理扣时（30分钟/人）",
        ),
        sa.Column(
            "negative_review_penalty_hours",
            sa.Float(),
            server_default="0.0",
            comment="差评扣时（60分钟/单/人）",
        ),
        sa.Column(
            "total_work_days",
            sa.Integer(),
            server_default="0",
            comment="Total work days in the month",
        ),
        sa.Column(
            "attended_days",
            sa.Integer(),
            server_default="0",
            comment="Days with attendance records",
        ),
        sa.Column(
            "late_days",
            sa.Integer(),
            server_default="0",
            comment="Days with late check-in",
        ),
        sa.Column(
            "early_checkout_days",
            sa.Integer(),
            server_default="0",
            comment="Days with early checkout",
        ),
        sa.Column(
            "task_completion_count",
            sa.Integer(),
            server_default="0",
            comment="Number of completed tasks",
        ),
        sa.Column(
            "average_task_rating",
            sa.Float(),
            nullable=True,
            comment="Average rating for completed tasks",
        ),
        sa.Column(
            "summary_notes", sa.Text(), nullable=True, comment="Monthly summary notes"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record creation timestamp",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Record last update timestamp",
        ),
        sa.ForeignKeyConstraint(
            ["member_id"],
            ["members.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "member_id", "year", "month", name="uq_attendance_summary_member_month"
        ),
        comment="Monthly attendance summaries table",
    )
    op.create_index(
        op.f("ix_monthly_attendance_summaries_id"),
        "monthly_attendance_summaries",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_monthly_attendance_summaries_member_id"),
        "monthly_attendance_summaries",
        ["member_id"],
        unique=False,
    )
    op.create_index(
        "idx_summary_year_month",
        "monthly_attendance_summaries",
        ["year", "month"],
        unique=False,
    )
    op.create_index(
        "idx_summary_member_year",
        "monthly_attendance_summaries",
        ["member_id", "year"],
        unique=False,
    )

    # Insert default admin user
    op.execute(
        """
        INSERT INTO members (
            username, name, student_id, phone, email, department, class_name, 
            join_date, password_hash, role, is_active, profile_completed, is_verified, login_count
        ) VALUES (
            'admin', 
            '系统管理员', 
            'admin', 
            NULL,
            'admin@example.com',
            '信息化建设处', 
            '管理员',
            CURRENT_DATE,
            '$2b$12$Ke3Lf5m5nKCTb8LUADjzJu3CqgGk8zvFfW3CQvn5f4eKdfgY5G4YS',  -- password: admin123
            'admin',
            true,
            true,
            true,
            0
        ) ON CONFLICT (username) DO NOTHING
    """
    )

    # Insert default task tags
    op.execute(
        """
        INSERT INTO task_tags (name, description, work_minutes_modifier, tag_type, is_active) VALUES
        ('爆单任务', '爆单任务标记，独立计算工时15分钟', 15, 'rush_order', true),
        ('非默认好评', '用户给出非默认好评，奖励30分钟', 30, 'non_default_rating', true),
        ('超时响应', '响应超过24小时，扣除30分钟', -30, 'timeout_response', true),
        ('超时处理', '处理超过48小时，扣除30分钟', -30, 'timeout_processing', true),
        ('差评', '用户差评（2星及以下），扣除60分钟', -60, 'bad_rating', true)
        ON CONFLICT (name) DO NOTHING
    """
    )


def downgrade() -> None:
    """Drop all tables in reverse creation order."""

    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table("monthly_attendance_summaries")
    op.drop_table("attendance_exceptions")
    op.drop_table("attendance_records")
    op.drop_table("task_tag_associations")
    op.drop_table("assistance_tasks")
    op.drop_table("monitoring_tasks")
    op.drop_table("repair_tasks")
    op.drop_table("task_tags")
    op.drop_table("members")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS attendanceexceptionstatus")
    op.execute("DROP TYPE IF EXISTS tasktagtype")
    op.execute("DROP TYPE IF EXISTS tasktype")
    op.execute("DROP TYPE IF EXISTS taskpriority")
    op.execute("DROP TYPE IF EXISTS taskcategory")
    op.execute("DROP TYPE IF EXISTS taskstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
