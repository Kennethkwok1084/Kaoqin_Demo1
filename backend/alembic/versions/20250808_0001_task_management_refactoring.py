"""task_management_refactoring

Revision ID: 20250808_0001
Revises: 48a1baba958a
Create Date: 2025-08-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20250808_0001'
down_revision: Union[str, None] = '48a1baba958a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add refactored task management fields."""
    
    # Add new fields to repair_tasks table for enhanced A/B table matching and import
    op.add_column('repair_tasks', sa.Column('original_data', sa.JSON(), nullable=True, comment='A表原始数据完整保存'))
    op.add_column('repair_tasks', sa.Column('matched_member_data', sa.JSON(), nullable=True, comment='B表匹配的成员数据'))
    op.add_column('repair_tasks', sa.Column('is_rush_order', sa.Boolean(), nullable=False, server_default='false', comment='爆单标记，独立计算工时'))
    op.add_column('repair_tasks', sa.Column('work_order_status', sa.String(length=50), nullable=True, comment='A表工单状态（用于状态映射）'))
    op.add_column('repair_tasks', sa.Column('repair_form', sa.String(length=50), nullable=True, comment='B表检修形式（用于线上/线下判断）'))
    
    # Create indexes for new fields to improve query performance
    op.create_index('idx_repair_tasks_is_rush_order', 'repair_tasks', ['is_rush_order'])
    op.create_index('idx_repair_tasks_work_order_status', 'repair_tasks', ['work_order_status'])
    
    # Update existing task_tags table to support new TaskTagType enum values
    # Note: In PostgreSQL, we need to add new enum values to the existing enum type
    # This is done via raw SQL since SQLAlchemy doesn't handle enum alterations well
    
    # First, check if the enum type exists and add new values
    op.execute("""
        DO $$
        BEGIN
            -- Add new enum values for TaskTagType if they don't exist
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'rush_order' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'rush_order';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'non_default_rating' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'non_default_rating';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'timeout_response' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'timeout_response';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'timeout_processing' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'timeout_processing';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'bad_rating' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'bad_rating';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'bonus' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'bonus';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'penalty' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'penalty';
            END IF;
            
            IF NOT EXISTS (SELECT 1 FROM pg_enum WHERE enumlabel = 'category' AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'tasktag_type')) THEN
                ALTER TYPE tasktag_type ADD VALUE 'category';
            END IF;
        EXCEPTION
            WHEN others THEN
                -- If the enum type doesn't exist yet, it will be created by the model
                NULL;
        END $$;
    """)
    
    # Insert standard task tags for the refactored system
    op.execute("""
        INSERT INTO task_tags (name, description, work_minutes_modifier, tag_type, is_active, created_at, updated_at)
        VALUES 
            ('爆单任务', '爆单任务标记，独立计算工时15分钟', 15, 'rush_order', true, NOW(), NOW()),
            ('非默认好评', '用户给出非默认好评，奖励30分钟', 30, 'non_default_rating', true, NOW(), NOW()),
            ('超时响应', '响应超过24小时，扣除30分钟', -30, 'timeout_response', true, NOW(), NOW()),
            ('超时处理', '处理超过48小时，扣除30分钟', -30, 'timeout_processing', true, NOW(), NOW()),
            ('差评', '用户差评（2星及以下），扣除60分钟', -60, 'bad_rating', true, NOW(), NOW())
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove refactored task management fields."""
    
    # Remove indexes
    op.drop_index('idx_repair_tasks_work_order_status', table_name='repair_tasks')
    op.drop_index('idx_repair_tasks_is_rush_order', table_name='repair_tasks')
    
    # Remove columns from repair_tasks table
    op.drop_column('repair_tasks', 'repair_form')
    op.drop_column('repair_tasks', 'work_order_status')
    op.drop_column('repair_tasks', 'is_rush_order')
    op.drop_column('repair_tasks', 'matched_member_data')
    op.drop_column('repair_tasks', 'original_data')
    
    # Remove the standard task tags that were added
    op.execute("""
        DELETE FROM task_tags WHERE name IN (
            '爆单任务',
            '非默认好评', 
            '超时响应',
            '超时处理',
            '差评'
        );
    """)
    
    # Note: We don't remove the enum values as this can break existing data
    # and PostgreSQL doesn't support removing enum values easily