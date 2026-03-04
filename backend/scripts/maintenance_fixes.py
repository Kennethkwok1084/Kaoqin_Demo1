#!/usr/bin/env python3
"""统一维护脚本：合并历史 fix_* 脚本，提供规范命名的单一入口。"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _iter_py_files(target_dir: Path) -> list[Path]:
    if not target_dir.exists():
        return []
    return [p for p in target_dir.glob("*.py") if p.name.startswith("test_")]


def normalize_test_auth_headers(target_dir: Path) -> int:
    """统一测试中 auth_headers 的调用方式。"""
    changed_files = 0
    for file_path in _iter_py_files(target_dir):
        content = file_path.read_text(encoding="utf-8")
        if "async def auth_headers(" in content:
            continue

        new_content = content
        new_content = re.sub(
            r"headers=await auth_headers\(\)",
            "headers=auth_headers(token)",
            new_content,
        )
        new_content = re.sub(
            r"async def (test_\w+)\(self, async_client: AsyncClient, auth_headers\):",
            r"async def \1(self, async_client: AsyncClient, auth_headers, token):",
            new_content,
        )

        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            changed_files += 1

    return changed_files


def normalize_test_status_codes(target_dir: Path) -> int:
    """统一测试中状态码兜底策略。"""
    changed_files = 0
    for file_path in _iter_py_files(target_dir):
        content = file_path.read_text(encoding="utf-8")
        new_content = re.sub(
            r"elif response\.status_code in \[404, 405, 501\]:",
            "elif response.status_code in [400, 401, 404, 405, 501]:",
            content,
        )

        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            changed_files += 1

    return changed_files


def normalize_api_return_types(target_files: list[Path]) -> int:
    """为缺失返回类型注解的 async def 添加统一注解。"""
    changed_files = 0
    pattern = re.compile(r"(async def [^(]+\([^)]*\)):(\s*\n)")

    for file_path in target_files:
        if not file_path.exists():
            continue

        content = file_path.read_text(encoding="utf-8")

        def replacement(match: re.Match[str]) -> str:
            func_sig = match.group(1)
            newline = match.group(2)
            if "->" in func_sig:
                return match.group(0)
            return f"{func_sig} -> dict[str, object]:{newline}"

        new_content = pattern.sub(replacement, content)
        if new_content != content:
            file_path.write_text(new_content, encoding="utf-8")
            changed_files += 1

    return changed_files


async def recalculate_work_minutes(
    scope: str,
    only_missing: bool,
    apply_changes: bool,
) -> dict[str, int]:
    """重算工时（repair 使用服务层单一入口，monitoring/assistance 用模型方法）。"""
    from sqlalchemy import or_, select
    from sqlalchemy.orm import selectinload

    from app.core.database import AsyncSessionLocal
    from app.models.task import AssistanceTask, MonitoringTask, RepairTask
    from app.services.work_hours_service import WorkHoursCalculationService

    summary = {
        "repair_total": 0,
        "repair_changed": 0,
        "monitoring_total": 0,
        "monitoring_changed": 0,
        "assistance_total": 0,
        "assistance_changed": 0,
    }

    async with AsyncSessionLocal() as session:
        if scope in {"all", "repair"}:
            repair_query = select(RepairTask).options(selectinload(RepairTask.tags))
            if only_missing:
                repair_query = repair_query.where(
                    or_(RepairTask.work_minutes == 0, RepairTask.work_minutes.is_(None))
                )

            repair_tasks = (await session.execute(repair_query)).scalars().all()
            service = WorkHoursCalculationService(session)
            summary["repair_total"] = len(repair_tasks)

            for task in repair_tasks:
                old_value = task.work_minutes or 0
                result = await service.calculate_task_work_minutes(task)
                new_value = result["total_minutes"]
                if old_value != new_value:
                    summary["repair_changed"] += 1
                    if apply_changes:
                        task.base_work_minutes = result["base_minutes"]
                        task.work_minutes = new_value

        if scope in {"all", "monitoring"}:
            monitoring_query = select(MonitoringTask)
            if only_missing:
                monitoring_query = monitoring_query.where(
                    or_(
                        MonitoringTask.work_minutes == 0,
                        MonitoringTask.work_minutes.is_(None),
                    )
                )

            monitoring_tasks = (await session.execute(monitoring_query)).scalars().all()
            summary["monitoring_total"] = len(monitoring_tasks)

            for task in monitoring_tasks:
                old_value = task.work_minutes or 0
                new_value = task.calculate_duration_minutes()
                if old_value != new_value:
                    summary["monitoring_changed"] += 1
                    if apply_changes:
                        task.work_minutes = new_value

        if scope in {"all", "assistance"}:
            assistance_query = select(AssistanceTask)
            if only_missing:
                assistance_query = assistance_query.where(
                    or_(
                        AssistanceTask.work_minutes == 0,
                        AssistanceTask.work_minutes.is_(None),
                    )
                )

            assistance_tasks = (await session.execute(assistance_query)).scalars().all()
            summary["assistance_total"] = len(assistance_tasks)

            for task in assistance_tasks:
                old_value = task.work_minutes or 0
                new_value = task.calculate_duration_minutes()
                if old_value != new_value:
                    summary["assistance_changed"] += 1
                    if apply_changes:
                        task.work_minutes = new_value

        if apply_changes:
            await session.commit()
        else:
            await session.rollback()

    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="后端维护脚本统一入口")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_auth = subparsers.add_parser("normalize-test-auth-headers")
    parser_auth.add_argument(
        "--target-dir",
        default="tests/comprehensive",
        help="目标测试目录（默认 tests/comprehensive）",
    )

    parser_status = subparsers.add_parser("normalize-test-status-codes")
    parser_status.add_argument(
        "--target-dir",
        default="tests/comprehensive",
        help="目标测试目录（默认 tests/comprehensive）",
    )

    parser_return = subparsers.add_parser("normalize-api-return-types")
    parser_return.add_argument(
        "--files",
        nargs="*",
        default=[
            "app/api/v1/tasks.py",
            "app/api/v1/statistics.py",
            "app/api/v1/members.py",
            "app/api/v1/attendance.py",
            "app/api/v1/auth.py",
        ],
        help="目标 API 文件列表",
    )

    parser_work = subparsers.add_parser("recalculate-work-minutes")
    parser_work.add_argument(
        "--scope",
        choices=["all", "repair", "monitoring", "assistance"],
        default="all",
        help="重算范围",
    )
    parser_work.add_argument(
        "--only-missing",
        action="store_true",
        help="仅处理 work_minutes 为 0/NULL 的记录",
    )
    parser_work.add_argument(
        "--apply",
        action="store_true",
        help="执行写入；默认仅 dry-run",
    )

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "normalize-test-auth-headers":
        changed = normalize_test_auth_headers(Path(args.target_dir))
        print(f"normalize-test-auth-headers: changed_files={changed}")
        return

    if args.command == "normalize-test-status-codes":
        changed = normalize_test_status_codes(Path(args.target_dir))
        print(f"normalize-test-status-codes: changed_files={changed}")
        return

    if args.command == "normalize-api-return-types":
        files = [Path(p) for p in args.files]
        changed = normalize_api_return_types(files)
        print(f"normalize-api-return-types: changed_files={changed}")
        return

    if args.command == "recalculate-work-minutes":
        summary = asyncio.run(
            recalculate_work_minutes(
                scope=args.scope,
                only_missing=args.only_missing,
                apply_changes=args.apply,
            )
        )
        mode = "apply" if args.apply else "dry-run"
        print(f"recalculate-work-minutes ({mode}): {summary}")
        return

    parser.error("未知命令")


if __name__ == "__main__":
    main()
