#!/usr/bin/env python3
"""
修复任务工时计算问题
重新计算所有任务的work_minutes字段
"""

import asyncio
import sys
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from app.models.task import RepairTask, MonitoringTask, AssistanceTask
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def fix_repair_task_work_minutes():
    """修复报修任务的工时计算"""
    logger.info("开始修复报修任务工时...")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        try:
            # 查询所有work_minutes为0或None的任务
            query = select(RepairTask).where(
                (RepairTask.work_minutes == 0) | (RepairTask.work_minutes.is_(None))
            )

            result = await db.execute(query)
            tasks = result.scalars().all()

            logger.info(f"找到 {len(tasks)} 个需要修复的报修任务")

            fixed_count = 0
            for task in tasks:
                old_work_minutes = task.work_minutes

                # 手动计算基础工时
                task.base_work_minutes = task.get_base_work_minutes()

                # 重新计算总工时
                task.work_minutes = task.calculate_work_minutes()

                logger.info(
                    f"任务 {task.id}: {old_work_minutes} -> {task.work_minutes} 分钟 "
                    f"({task.task_type.value}, {task.status.value})"
                )

                fixed_count += 1

                # 每处理50个任务提交一次
                if fixed_count % 50 == 0:
                    await db.commit()
                    logger.info(f"已修复 {fixed_count} 个任务...")

            # 提交剩余更改
            await db.commit()
            logger.info(f"报修任务工时修复完成，共修复 {fixed_count} 个任务")

        except Exception as e:
            logger.error(f"修复报修任务工时时出错: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()

async def fix_monitoring_task_work_minutes():
    """修复监控任务的工时计算"""
    logger.info("开始修复监控任务工时...")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        try:
            query = select(MonitoringTask).where(
                (MonitoringTask.work_minutes == 0) | (MonitoringTask.work_minutes.is_(None))
            )

            result = await db.execute(query)
            tasks = result.scalars().all()

            logger.info(f"找到 {len(tasks)} 个需要修复的监控任务")

            fixed_count = 0
            for task in tasks:
                old_work_minutes = task.work_minutes

                # 监控任务使用实际持续时间或默认值
                if task.start_time and task.end_time:
                    duration = task.end_time - task.start_time
                    task.work_minutes = max(1, int(duration.total_seconds() / 60))
                else:
                    # 默认监控任务30分钟
                    task.work_minutes = 30

                logger.info(f"监控任务 {task.id}: {old_work_minutes} -> {task.work_minutes} 分钟")
                fixed_count += 1

                if fixed_count % 50 == 0:
                    await db.commit()
                    logger.info(f"已修复 {fixed_count} 个监控任务...")

            await db.commit()
            logger.info(f"监控任务工时修复完成，共修复 {fixed_count} 个任务")

        except Exception as e:
            logger.error(f"修复监控任务工时时出错: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()

async def fix_assistance_task_work_minutes():
    """修复协助任务的工时计算"""
    logger.info("开始修复协助任务工时...")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        try:
            query = select(AssistanceTask).where(
                (AssistanceTask.work_minutes == 0) | (AssistanceTask.work_minutes.is_(None))
            )

            result = await db.execute(query)
            tasks = result.scalars().all()

            logger.info(f"找到 {len(tasks)} 个需要修复的协助任务")

            fixed_count = 0
            for task in tasks:
                old_work_minutes = task.work_minutes

                # 协助任务使用实际持续时间或默认值
                if task.start_time and task.end_time:
                    duration = task.end_time - task.start_time
                    task.work_minutes = max(1, int(duration.total_seconds() / 60))
                else:
                    # 默认协助任务60分钟
                    task.work_minutes = 60

                logger.info(f"协助任务 {task.id}: {old_work_minutes} -> {task.work_minutes} 分钟")
                fixed_count += 1

                if fixed_count % 50 == 0:
                    await db.commit()
                    logger.info(f"已修复 {fixed_count} 个协助任务...")

            await db.commit()
            logger.info(f"协助任务工时修复完成，共修复 {fixed_count} 个任务")

        except Exception as e:
            logger.error(f"修复协助任务工时时出错: {e}")
            await db.rollback()
            raise
        finally:
            await engine.dispose()

async def verify_fix():
    """验证修复结果"""
    logger.info("验证修复结果...")

    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession)

    async with async_session() as db:
        try:
            # 统计报修任务
            repair_query = select(RepairTask).where(RepairTask.work_minutes == 0)
            repair_result = await db.execute(repair_query)
            repair_count = len(repair_result.scalars().all())

            # 统计监控任务
            monitoring_query = select(MonitoringTask).where(MonitoringTask.work_minutes == 0)
            monitoring_result = await db.execute(monitoring_query)
            monitoring_count = len(monitoring_result.scalars().all())

            # 统计协助任务
            assistance_query = select(AssistanceTask).where(AssistanceTask.work_minutes == 0)
            assistance_result = await db.execute(assistance_query)
            assistance_count = len(assistance_result.scalars().all())

            logger.info("修复后统计:")
            logger.info(f"  - 报修任务work_minutes=0的数量: {repair_count}")
            logger.info(f"  - 监控任务work_minutes=0的数量: {monitoring_count}")
            logger.info(f"  - 协助任务work_minutes=0的数量: {assistance_count}")

            # 展示一个修复后的示例
            sample_query = select(RepairTask).where(
                RepairTask.work_minutes > 0
            ).order_by(RepairTask.id.desc()).limit(1)

            sample_result = await db.execute(sample_query)
            sample_task = sample_result.scalar_one_or_none()

            if sample_task:
                logger.info(f"修复示例 - 任务 {sample_task.id}:")
                logger.info(f"  - 类型: {sample_task.task_type.value}")
                logger.info(f"  - 基础工时: {sample_task.base_work_minutes} 分钟")
                logger.info(f"  - 实际工时: {sample_task.work_minutes} 分钟")
                logger.info(f"  - 预估工时: {sample_task.base_work_minutes/60:.2f} 小时")
                logger.info(f"  - 实际工时: {sample_task.work_minutes/60:.2f} 小时")

        except Exception as e:
            logger.error(f"验证时出错: {e}")
            raise
        finally:
            await engine.dispose()

async def main():
    """主函数"""
    logger.info("开始修复所有任务的工时计算问题...")

    try:
        # 修复不同类型的任务
        await fix_repair_task_work_minutes()
        await fix_monitoring_task_work_minutes()
        await fix_assistance_task_work_minutes()

        # 验证修复结果
        await verify_fix()

        logger.info("所有任务工时修复完成!")

    except Exception as e:
        logger.error(f"修复过程中出现错误: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())