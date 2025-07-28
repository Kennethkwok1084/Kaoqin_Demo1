"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-01-27 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create members table
    op.create_table('members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Member name'),
        sa.Column('student_id', sa.String(length=20), nullable=False, comment='Student ID (unique identifier)'),
        sa.Column('group_id', sa.Integer(), nullable=True, comment='Group ID (work group assignment)'),
        sa.Column('class_name', sa.String(length=50), nullable=True, comment='Class name'),
        sa.Column('dormitory', sa.Text(), nullable=True, comment='Dormitory information (encrypted)'),
        sa.Column('phone', sa.Text(), nullable=True, comment='Phone number (encrypted)'),
        sa.Column('email', sa.String(length=100), nullable=True, comment='Email address'),
        sa.Column('password_hash', sa.String(length=255), nullable=False, comment='Hashed password'),
        sa.Column('role', sa.Enum('ADMIN', 'GROUP_LEADER', 'MEMBER', 'GUEST', name='userrole'), nullable=False, comment='User role'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether the member is active'),
        sa.Column('is_verified', sa.Boolean(), nullable=False, comment='Whether the member email is verified'),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True, comment='Last login timestamp'),
        sa.Column('login_count', sa.Integer(), nullable=False, comment='Total login count'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id', name='pk_members'),
        sa.UniqueConstraint('student_id', name='uq_member_student_id'),
        comment='Team members table'
    )
    op.create_index(op.f('ix_members_email'), 'members', ['email'], unique=False)
    op.create_index(op.f('ix_members_id'), 'members', ['id'], unique=False)
    op.create_index(op.f('ix_members_name'), 'members', ['name'], unique=False)
    op.create_index(op.f('ix_members_student_id'), 'members', ['student_id'], unique=False)

    # Create task_tags table
    op.create_table('task_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('name', sa.String(length=50), nullable=False, comment='Tag name'),
        sa.Column('description', sa.Text(), nullable=True, comment='Tag description'),
        sa.Column('work_minutes_modifier', sa.Integer(), nullable=False, comment='Work minutes modifier (+/- minutes)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether the tag is active'),
        sa.Column('tag_type', sa.String(length=30), nullable=True, comment='Tag type (bonus, penalty, category)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id', name='pk_task_tags'),
        sa.UniqueConstraint('name', name='uq_task_tags_name'),
        comment='Task tags for categorizing and calculating work hours'
    )
    op.create_index(op.f('ix_task_tags_id'), 'task_tags', ['id'], unique=False)
    op.create_index(op.f('ix_task_tags_name'), 'task_tags', ['name'], unique=False)

    # Create repair_tasks table
    op.create_table('repair_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('task_id', sa.String(length=50), nullable=False, comment='External task ID from work order system'),
        sa.Column('member_id', sa.Integer(), nullable=False, comment='Assigned member ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Task title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Detailed task description'),
        sa.Column('location', sa.String(length=200), nullable=True, comment='Task location'),
        sa.Column('category', sa.Enum('NETWORK_REPAIR', 'HARDWARE_REPAIR', 'SOFTWARE_SUPPORT', 'MONITORING', 'ASSISTANCE', 'OTHER', name='taskcategory'), nullable=False, comment='Task category'),
        sa.Column('priority', sa.Enum('LOW', 'MEDIUM', 'HIGH', 'URGENT', name='taskpriority'), nullable=False, comment='Task priority'),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'ON_HOLD', name='taskstatus'), nullable=False, comment='Task status'),
        sa.Column('task_type', sa.Enum('ONLINE', 'OFFLINE', name='tasktype'), nullable=False, comment='Task type (online/offline)'),
        sa.Column('report_time', sa.DateTime(timezone=True), nullable=False, comment='Task report time'),
        sa.Column('response_time', sa.DateTime(timezone=True), nullable=True, comment='Task response time'),
        sa.Column('completion_time', sa.DateTime(timezone=True), nullable=True, comment='Task completion time'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='User feedback'),
        sa.Column('rating', sa.Integer(), nullable=True, comment='User rating (1-5 stars)'),
        sa.Column('reporter_name', sa.String(length=50), nullable=True, comment='Reporter name'),
        sa.Column('reporter_contact', sa.String(length=100), nullable=True, comment='Reporter contact information'),
        sa.Column('work_minutes', sa.Integer(), nullable=False, comment='Calculated work minutes'),
        sa.Column('base_work_minutes', sa.Integer(), nullable=False, comment='Base work minutes before modifiers'),
        sa.Column('import_batch_id', sa.String(length=50), nullable=True, comment='Import batch ID for tracking'),
        sa.Column('is_matched', sa.Boolean(), nullable=False, comment='Whether task was matched during import'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_repair_tasks_member_id_members'),
        sa.PrimaryKeyConstraint('id', name='pk_repair_tasks'),
        sa.UniqueConstraint('task_id', name='uq_repair_task_task_id'),
        comment='Repair tasks table'
    )
    op.create_index('idx_repair_task_import_batch', 'repair_tasks', ['import_batch_id'], unique=False)
    op.create_index('idx_repair_task_member_status', 'repair_tasks', ['member_id', 'status'], unique=False)
    op.create_index('idx_repair_task_report_time', 'repair_tasks', ['report_time'], unique=False)
    op.create_index(op.f('ix_repair_tasks_id'), 'repair_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_repair_tasks_member_id'), 'repair_tasks', ['member_id'], unique=False)
    op.create_index(op.f('ix_repair_tasks_status'), 'repair_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_repair_tasks_task_id'), 'repair_tasks', ['task_id'], unique=False)

    # Create monitoring_tasks table
    op.create_table('monitoring_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('member_id', sa.Integer(), nullable=False, comment='Assigned member ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Task title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Task description'),
        sa.Column('location', sa.String(length=200), nullable=True, comment='Monitoring location'),
        sa.Column('monitoring_type', sa.String(length=50), nullable=False, comment='Monitoring type (inspection, maintenance, etc.)'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='Task start time'),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False, comment='Task end time'),
        sa.Column('work_minutes', sa.Integer(), nullable=False, comment='Actual work minutes'),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'ON_HOLD', name='taskstatus'), nullable=False, comment='Task status'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_monitoring_tasks_member_id_members'),
        sa.PrimaryKeyConstraint('id', name='pk_monitoring_tasks'),
        comment='Monitoring tasks table'
    )
    op.create_index('idx_monitoring_task_member_time', 'monitoring_tasks', ['member_id', 'start_time'], unique=False)
    op.create_index(op.f('ix_monitoring_tasks_id'), 'monitoring_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_monitoring_tasks_member_id'), 'monitoring_tasks', ['member_id'], unique=False)

    # Create assistance_tasks table
    op.create_table('assistance_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('member_id', sa.Integer(), nullable=False, comment='Assisting member ID'),
        sa.Column('title', sa.String(length=200), nullable=False, comment='Assistance task title'),
        sa.Column('description', sa.Text(), nullable=True, comment='Task description'),
        sa.Column('assisted_department', sa.String(length=100), nullable=True, comment='Assisted department/team'),
        sa.Column('assisted_person', sa.String(length=50), nullable=True, comment='Assisted person name'),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False, comment='Task start time'),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False, comment='Task end time'),
        sa.Column('work_minutes', sa.Integer(), nullable=False, comment='Assistance work minutes'),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'ON_HOLD', name='taskstatus'), nullable=False, comment='Task status'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_assistance_tasks_member_id_members'),
        sa.PrimaryKeyConstraint('id', name='pk_assistance_tasks'),
        comment='Assistance tasks table'
    )
    op.create_index('idx_assistance_task_member_time', 'assistance_tasks', ['member_id', 'start_time'], unique=False)
    op.create_index(op.f('ix_assistance_tasks_id'), 'assistance_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_assistance_tasks_member_id'), 'assistance_tasks', ['member_id'], unique=False)

    # Create attendance_records table
    op.create_table('attendance_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('member_id', sa.Integer(), nullable=False, comment='Member ID'),
        sa.Column('month', sa.String(length=7), nullable=False, comment='Month in YYYY-MM format'),
        sa.Column('repair_task_hours', sa.Float(), nullable=False, comment='Repair task hours for the month'),
        sa.Column('monitoring_hours', sa.Float(), nullable=False, comment='Monitoring task hours for the month'),
        sa.Column('assistance_hours', sa.Float(), nullable=False, comment='Assistance task hours for the month'),
        sa.Column('carried_hours', sa.Float(), nullable=False, comment='Hours carried from previous month'),
        sa.Column('total_hours', sa.Float(), nullable=False, comment='Total work hours (all categories + carried)'),
        sa.Column('remaining_hours', sa.Float(), nullable=False, comment='Remaining hours for next month'),
        sa.Column('details', sa.Text(), nullable=True, comment='Detailed calculation breakdown (JSON format)'),
        sa.Column('calculation_date', sa.DateTime(timezone=True), nullable=True, comment='When the calculation was performed'),
        sa.Column('is_final', sa.Boolean(), nullable=False, comment='Whether this record is finalized'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.ForeignKeyConstraint(['member_id'], ['members.id'], name='fk_attendance_records_member_id_members'),
        sa.PrimaryKeyConstraint('id', name='pk_attendance_records'),
        sa.UniqueConstraint('member_id', 'month', name='uq_attendance_member_month'),
        comment='Monthly attendance records table'
    )
    op.create_index('idx_attendance_member_month', 'attendance_records', ['member_id', 'month'], unique=False)
    op.create_index('idx_attendance_month', 'attendance_records', ['month'], unique=False)
    op.create_index(op.f('ix_attendance_records_id'), 'attendance_records', ['id'], unique=False)
    op.create_index(op.f('ix_attendance_records_member_id'), 'attendance_records', ['member_id'], unique=False)

    # Create attendance_configurations table
    op.create_table('attendance_configurations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, comment='Primary key'),
        sa.Column('config_key', sa.String(length=50), nullable=False, comment='Configuration key'),
        sa.Column('config_value', sa.String(length=200), nullable=False, comment='Configuration value'),
        sa.Column('description', sa.Text(), nullable=True, comment='Configuration description'),
        sa.Column('value_type', sa.String(length=20), nullable=False, comment='Value data type (int, float, string, bool)'),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether this configuration is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record creation timestamp'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Record last update timestamp'),
        sa.PrimaryKeyConstraint('id', name='pk_attendance_configurations'),
        sa.UniqueConstraint('config_key', name='uq_attendance_config_key'),
        comment='Attendance calculation configurations'
    )
    op.create_index(op.f('ix_attendance_configurations_config_key'), 'attendance_configurations', ['config_key'], unique=False)
    op.create_index(op.f('ix_attendance_configurations_id'), 'attendance_configurations', ['id'], unique=False)

    # Create task_tag_associations table (many-to-many)
    op.create_table('task_tag_associations',
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['tag_id'], ['task_tags.id'], name='fk_task_tag_associations_tag_id_task_tags'),
        sa.ForeignKeyConstraint(['task_id'], ['repair_tasks.id'], name='fk_task_tag_associations_task_id_repair_tasks'),
        sa.PrimaryKeyConstraint('task_id', 'tag_id', name='pk_task_tag_associations'),
        comment='Association table for tasks and tags'
    )

    # Set default values for enums and booleans
    op.execute("ALTER TABLE members ALTER COLUMN role SET DEFAULT 'MEMBER'")
    op.execute("ALTER TABLE members ALTER COLUMN is_active SET DEFAULT true")
    op.execute("ALTER TABLE members ALTER COLUMN is_verified SET DEFAULT false")
    op.execute("ALTER TABLE members ALTER COLUMN login_count SET DEFAULT 0")
    
    op.execute("ALTER TABLE task_tags ALTER COLUMN work_minutes_modifier SET DEFAULT 0")
    op.execute("ALTER TABLE task_tags ALTER COLUMN is_active SET DEFAULT true")
    
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN category SET DEFAULT 'NETWORK_REPAIR'")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN priority SET DEFAULT 'MEDIUM'")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN status SET DEFAULT 'PENDING'")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN task_type SET DEFAULT 'ONLINE'")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN work_minutes SET DEFAULT 0")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN base_work_minutes SET DEFAULT 0")
    op.execute("ALTER TABLE repair_tasks ALTER COLUMN is_matched SET DEFAULT false")
    
    op.execute("ALTER TABLE monitoring_tasks ALTER COLUMN status SET DEFAULT 'COMPLETED'")
    op.execute("ALTER TABLE assistance_tasks ALTER COLUMN status SET DEFAULT 'COMPLETED'")
    
    op.execute("ALTER TABLE attendance_records ALTER COLUMN repair_task_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN monitoring_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN assistance_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN carried_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN total_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN remaining_hours SET DEFAULT 0.0")
    op.execute("ALTER TABLE attendance_records ALTER COLUMN is_final SET DEFAULT false")
    
    op.execute("ALTER TABLE attendance_configurations ALTER COLUMN value_type SET DEFAULT 'string'")
    op.execute("ALTER TABLE attendance_configurations ALTER COLUMN is_active SET DEFAULT true")


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('task_tag_associations')
    op.drop_table('attendance_configurations')
    op.drop_table('attendance_records')
    op.drop_table('assistance_tasks')
    op.drop_table('monitoring_tasks')
    op.drop_table('repair_tasks')
    op.drop_table('task_tags')
    op.drop_table('members')
    
    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS userrole')
    op.execute('DROP TYPE IF EXISTS taskcategory')
    op.execute('DROP TYPE IF EXISTS taskpriority')
    op.execute('DROP TYPE IF EXISTS taskstatus')
    op.execute('DROP TYPE IF EXISTS tasktype')