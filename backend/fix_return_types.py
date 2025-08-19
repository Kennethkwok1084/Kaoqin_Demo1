#!/usr/bin/env python3
"""
Quick script to add missing return type annotations to API endpoints
"""

import re
from pathlib import Path


def fix_return_types_in_file(file_path: Path):
    """Fix missing return type annotations in a single file"""
    if not file_path.exists():
        return

    content = file_path.read_text(encoding="utf-8")

    # Pattern to match async def without return type annotation
    pattern = r"(async def [^(]+\([^)]*\)):(\s*\n)"

    def replacement(match):
        func_sig = match.group(1)
        newline = match.group(2)

        # Skip if already has return type annotation
        if "->" in func_sig:
            return match.group(0)

        # Add return type annotation
        return f"{func_sig} -> Dict[str, Any]:{newline}"

    new_content = re.sub(pattern, replacement, content)

    if new_content != content:
        file_path.write_text(new_content, encoding="utf-8")
        print(f"Fixed return types in {file_path}")


def main():
    """Fix return types in key API files"""
    backend_dir = Path(__file__).parent
    api_files = [
        backend_dir / "app" / "api" / "v1" / "tasks.py",
        backend_dir / "app" / "api" / "v1" / "statistics.py",
        backend_dir / "app" / "api" / "v1" / "members.py",
        backend_dir / "app" / "api" / "v1" / "attendance.py",
        backend_dir / "app" / "api" / "v1" / "auth.py",
    ]

    for file_path in api_files:
        fix_return_types_in_file(file_path)


if __name__ == "__main__":
    main()
