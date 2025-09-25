#!/usr/bin/env python3
"""
简化的工时修复脚本 - 直接使用SQL更新
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

async def fix_work_minutes_direct():
    """直接使用SQL修复工时"""
    logger.info("开始使用SQL直接修复工时...")

    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        try:
            # 查询需要修复的报修任务数量
            result = await conn.execute(
                text("SELECT COUNT(*) FROM repair_tasks WHERE work_minutes = 0 OR work_minutes IS NULL")
            )
            repair_count = result.scalar()
            logger.info(f"发现 {repair_count} 个报修任务需要修复工时")

            # 修复线上报修任务 (task_type = 'online')
            online_update = await conn.execute(
                text("""
                    UPDATE repair_tasks
                    SET work_minutes = 40,
                        base_work_minutes = 40
                    WHERE (work_minutes = 0 OR work_minutes IS NULL)
                    AND task_type = 'online'
                """)
            )
            logger.info(f"修复了 {online_update.rowcount} 个线上报修任务，设置为40分钟")

            # 修复线下报修任务 (task_type = 'offline')
            offline_update = await conn.execute(
                text("""
                    UPDATE repair_tasks
                    SET work_minutes = 100,
                        base_work_minutes = 100
                    WHERE (work_minutes = 0 OR work_minutes IS NULL)
                    AND task_type = 'offline'
                """)
            )
            logger.info(f"修复了 {offline_update.rowcount} 个线下报修任务，设置为100分钟")

            # 修复其他类型的报修任务（默认为线上）
            other_update = await conn.execute(
                text("""
                    UPDATE repair_tasks
                    SET work_minutes = 40,
                        base_work_minutes = 40
                    WHERE (work_minutes = 0 OR work_minutes IS NULL)
                    AND (task_type IS NULL OR task_type NOT IN ('online', 'offline'))
                """)
            )
            logger.info(f"修复了 {other_update.rowcount} 个其他报修任务，默认设置为40分钟")

            # 处理监控任务
            monitoring_result = await conn.execute(
                text("SELECT COUNT(*) FROM monitoring_tasks WHERE work_minutes = 0 OR work_minutes IS NULL")
            )
            monitoring_count = monitoring_result.scalar()
            if monitoring_count > 0:
                logger.info(f"发现 {monitoring_count} 个监控任务需要修复工时")
                monitoring_update = await conn.execute(
                    text("""
                        UPDATE monitoring_tasks
                        SET work_minutes = 30
                        WHERE work_minutes = 0 OR work_minutes IS NULL
                    """)
                )
                logger.info(f"修复了 {monitoring_update.rowcount} 个监控任务，设置为30分钟")

            # 处理协助任务
            assistance_result = await conn.execute(
                text("SELECT COUNT(*) FROM assistance_tasks WHERE work_minutes = 0 OR work_minutes IS NULL")
            )
            assistance_count = assistance_result.scalar()
            if assistance_count > 0:
                logger.info(f"发现 {assistance_count} 个协助任务需要修复工时")
                assistance_update = await conn.execute(
                    text("""
                        UPDATE assistance_tasks
                        SET work_minutes = 60
                        WHERE work_minutes = 0 OR work_minutes IS NULL
                    """)
                )
                logger.info(f"修复了 {assistance_update.rowcount} 个协助任务，设置为60分钟")

            logger.info("工时修复完成!")

        except Exception as e:
            logger.error(f"修复过程中出错: {e}")
            raise
        finally:
            await engine.dispose()

async def verify_fix():
    """验证修复结果"""
    logger.info("验证修复结果...")

    engine = create_async_engine(settings.DATABASE_URL)

    async with engine.begin() as conn:
        try:
            # 检查报修任务
            repair_result = await conn.execute(
                text("SELECT COUNT(*) FROM repair_tasks WHERE work_minutes = 0 OR work_minutes IS NULL")
            )
            repair_zero = repair_result.scalar()

            # 统计不同类型的报修任务工时
            online_result = await conn.execute(
                text("SELECT COUNT(*), AVG(work_minutes) FROM repair_tasks WHERE task_type = 'online' AND work_minutes > 0")
            )
            online_stats = online_result.fetchone()

            offline_result = await conn.execute(
                text("SELECT COUNT(*), AVG(work_minutes) FROM repair_tasks WHERE task_type = 'offline' AND work_minutes > 0")
            )
            offline_stats = offline_result.fetchone()

            # 展示示例
            sample_result = await conn.execute(
                text("""
                    SELECT id, task_type, base_work_minutes, work_minutes, status
                    FROM repair_tasks
                    WHERE work_minutes > 0
                    ORDER BY id DESC
                    LIMIT 3
                """)
            )
            samples = sample_result.fetchall()

            logger.info("修复结果验证:")
            logger.info(f"  - 报修任务work_minutes=0的数量: {repair_zero}")
            logger.info(f"  - 线上任务: {online_stats[0] if online_stats[0] else 0} 个, 平均工时: {online_stats[1] or 0:.1f} 分钟")
            logger.info(f"  - 线下任务: {offline_stats[0] if offline_stats[0] else 0} 个, 平均工时: {offline_stats[1] or 0:.1f} 分钟")

            logger.info("最近修复的任务示例:")
            for sample in samples:
                logger.info(f"  - 任务 {sample[0]}: {sample[1]}, 基础={sample[2]}分钟, 实际={sample[3]}分钟, 状态={sample[4]}")

        except Exception as e:
            logger.error(f"验证时出错: {e}")
            raise
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    try:
        await fix_work_minutes_direct()
        await verify_fix()
        logger.info("所有工时修复完成并验证成功!")
    except Exception as e:
        logger.error(f"修复失败: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())