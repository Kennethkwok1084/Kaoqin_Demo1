#!/usr/bin/env python3
"""
修复工时计算问题 - 考虑标签的影响
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_work_minutes_with_tags():
    """修复工时计算，考虑标签影响"""
    logger.info("开始修复工时计算（考虑标签影响）...")

    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        try:
            # 查询所有需要重新计算的任务
            tasks_result = await conn.execute(
                text("""
                    SELECT
                        rt.id,
                        rt.task_id,
                        rt.task_type,
                        rt.base_work_minutes,
                        rt.work_minutes,
                        COALESCE(SUM(tt.work_minutes_modifier), 0) as total_modifier
                    FROM repair_tasks rt
                    LEFT JOIN task_tag_associations tta ON rt.id = tta.task_id
                    LEFT JOIN task_tags tt ON tta.tag_id = tt.id AND tt.is_active = true
                    WHERE rt.work_minutes = 0 OR rt.work_minutes IS NULL
                    GROUP BY rt.id, rt.task_id, rt.task_type, rt.base_work_minutes, rt.work_minutes
                """)
            )

            tasks = tasks_result.fetchall()
            logger.info(f"找到 {len(tasks)} 个任务需要重新计算工时")

            fixed_count = 0
            for task in tasks:
                task_id, task_task_id, task_type, base_minutes, old_work_minutes, modifier = task

                # 计算基础工时
                if task_type == 'online':
                    base_work_minutes = 40
                elif task_type == 'offline':
                    base_work_minutes = 100
                else:
                    base_work_minutes = 40  # 默认

                # 应用标签修正
                final_work_minutes = max(0, base_work_minutes + (modifier or 0))

                # 更新数据库
                await conn.execute(
                    text("""
                        UPDATE repair_tasks
                        SET base_work_minutes = :base_minutes,
                            work_minutes = :work_minutes
                        WHERE id = :task_id
                    """),
                    {
                        'base_minutes': base_work_minutes,
                        'work_minutes': final_work_minutes,
                        'task_id': task_id
                    }
                )

                logger.info(
                    f"任务 {task_task_id} (ID:{task_id}): {task_type} "
                    f"基础={base_work_minutes}分钟, 修正={modifier or 0}分钟, "
                    f"最终={final_work_minutes}分钟 (之前={old_work_minutes}分钟)"
                )

                fixed_count += 1

            logger.info(f"工时修复完成，共修复 {fixed_count} 个任务")

        except Exception as e:
            logger.error(f"修复过程中出错: {e}")
            raise
        finally:
            await engine.dispose()

async def verify_fix_with_tags():
    """验证修复结果"""
    logger.info("验证修复结果（包含标签影响）...")

    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        try:
            # 检查特定任务71和72
            specific_result = await conn.execute(
                text("""
                    SELECT
                        rt.id,
                        rt.task_id,
                        rt.task_type,
                        rt.base_work_minutes,
                        rt.work_minutes,
                        STRING_AGG(tt.name, ', ') as tags,
                        COALESCE(SUM(tt.work_minutes_modifier), 0) as total_modifier
                    FROM repair_tasks rt
                    LEFT JOIN task_tag_associations tta ON rt.id = tta.task_id
                    LEFT JOIN task_tags tt ON tta.tag_id = tt.id AND tt.is_active = true
                    WHERE rt.id IN (71, 72)
                    GROUP BY rt.id, rt.task_id, rt.task_type, rt.base_work_minutes, rt.work_minutes
                    ORDER BY rt.id
                """)
            )

            specific_tasks = specific_result.fetchall()

            logger.info("特定任务验证 (71, 72):")
            for task in specific_tasks:
                task_id, task_task_id, task_type, base_minutes, work_minutes, tags, modifier = task
                logger.info(f"  任务 {task_task_id} (ID:{task_id}):")
                logger.info(f"    类型: {task_type}")
                logger.info(f"    基础工时: {base_minutes} 分钟")
                logger.info(f"    实际工时: {work_minutes} 分钟")
                logger.info(f"    标签: {tags or '无'}")
                logger.info(f"    标签修正: {modifier} 分钟")
                logger.info(f"    预期工时: {work_minutes} 分钟 (是否正确: {work_minutes == max(0, base_minutes + modifier)})")

            # 统计全部任务
            summary_result = await conn.execute(
                text("SELECT COUNT(*) as count FROM repair_tasks WHERE work_minutes = 0 OR work_minutes IS NULL")
            )
            zero_count = summary_result.scalar()

            logger.info(f"\\n总体统计:")
            logger.info(f"  仍有work_minutes=0的任务数量: {zero_count}")

        except Exception as e:
            logger.error(f"验证时出错: {e}")
            raise
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    try:
        await fix_work_minutes_with_tags()
        await verify_fix_with_tags()
        logger.info("工时修复完成!")
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())