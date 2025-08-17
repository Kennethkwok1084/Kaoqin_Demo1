#!/usr/bin/env python3
"""
Type checking validation script.
Runs MyPy on the codebase and reports type issues.
"""

import subprocess
import sys
from pathlib import Path


def run_mypy_check():
    """Run MyPy type checking on the codebase."""
    backend_dir = Path(__file__).parent.parent

    print("Running MyPy type checking...")
    print("=" * 50)

    # Try to run mypy
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "mypy",
                "app/",
                "--config-file",
                "mypy.ini",
                "--show-error-codes",
                "--show-error-context",
            ],
            cwd=backend_dir,
            capture_output=True,
            text=True,
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nReturn code: {result.returncode}")

        if result.returncode == 0:
            print("\n[SUCCESS] Type checking passed!")
        else:
            print("\n[FAILED] Type checking failed!")

        return result.returncode == 0

    except FileNotFoundError:
        print("[ERROR] MyPy not found. Please install it:")
        print("   pip install mypy")
        return False
    except Exception as e:
        print(f"[ERROR] Error running MyPy: {e}")
        return False


def check_common_type_issues():
    """Check for common type annotation issues."""
    backend_dir = Path(__file__).parent.parent
    app_dir = backend_dir / "app"

    print("\nChecking for common type issues...")
    print("=" * 50)

    issues = []

    # Check for Column vs Mapped issues
    for py_file in app_dir.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")

            # Check for old-style Column usage
            if "Column(" in content and "Mapped[" not in content:
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if "Column(" in line and not line.strip().startswith("#"):
                        issues.append(
                            f"{py_file.relative_to(backend_dir)}:{i} - Old Column style without Mapped annotation"
                        )

            # Check for missing return type annotations
            if "def " in content:
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    if (
                        line.strip().startswith("def ")
                        and " -> " not in line
                        and not line.endswith(":")
                    ):
                        if not any(
                            keyword in line
                            for keyword in ["__init__", "__str__", "__repr__"]
                        ):
                            issues.append(
                                f"{py_file.relative_to(backend_dir)}:{i} - Missing return type annotation"
                            )

        except Exception as e:
            print(f"Warning: Could not check {py_file}: {e}")

    if issues:
        print("\n[WARNING] Found potential type issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("\n[SUCCESS] No common type issues found!")

    return len(issues) == 0


def main():
    """Main function."""
    print("Type Checking Validation")
    print("=" * 50)

    mypy_ok = run_mypy_check()
    common_ok = check_common_type_issues()

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"MyPy check: {'[PASSED]' if mypy_ok else '[FAILED]'}")
    print(f"Common issues check: {'[PASSED]' if common_ok else '[FAILED]'}")

    if mypy_ok and common_ok:
        print("\n[SUCCESS] All type checks passed!")
        return 0
    else:
        print("\n[ERROR] Some type checks failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
