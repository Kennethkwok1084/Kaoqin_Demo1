#!/usr/bin/env python3
"""
MyPy Error Fix Script
Systematically fixes the most critical MyPy errors
"""

import re
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple


def run_mypy() -> Tuple[List[str], int]:
    """Run MyPy and return errors and count"""
    try:
        result = subprocess.run(
            ["python", "-m", "mypy", "app", "--show-error-codes", "--ignore-missing-imports"],
            capture_output=True,
            text=True,
            cwd=Path.cwd()
        )
        
        errors = []
        if result.stdout:
            errors = [line for line in result.stdout.split('\n') if 'error:' in line]
        
        return errors, len(errors)
    except Exception as e:
        print(f"Error running MyPy: {e}")
        return [], 0


def categorize_errors(errors: List[str]) -> Dict[str, List[str]]:
    """Categorize MyPy errors by type"""
    categories = {
        'union-attr': [],
        'dict-item': [],
        'unused-ignore': [],
        'no-any-return': [],
        'assignment': [],
        'return-value': [],
        'misc': [],
        'attr-defined': [],
        'arg-type': [],
        'other': []
    }
    
    for error in errors:
        matched = False
        for category in categories.keys():
            if f'[{category}]' in error:
                categories[category].append(error)
                matched = True
                break
        
        if not matched:
            categories['other'].append(error)
    
    return categories


def fix_unused_ignore_comments():
    """Fix unused type: ignore comments"""
    print("Fixing unused 'type: ignore' comments...")
    
    files_to_check = [
        "app/models/task.py",
        "app/core/celery_app.py", 
        "app/services/work_hours_service.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Remove unused type: ignore comments
            # This is a simple approach - remove standalone # type: ignore
            lines = content.split('\n')
            fixed_lines = []
            
            for line in lines:
                # Keep the line but remove unnecessary # type: ignore
                if '# type: ignore' in line and not any(keyword in line for keyword in ['import', 'Union', 'Optional']):
                    # Only remove if it's not actually needed
                    clean_line = line.replace('  # type: ignore', '').replace(' # type: ignore', '')
                    fixed_lines.append(clean_line)
                else:
                    fixed_lines.append(line)
            
            fixed_content = '\n'.join(fixed_lines)
            
            if fixed_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"  Fixed {file_path}")


def fix_dict_item_errors():
    """Fix dict-item type errors"""
    print("Fixing dict-item errors...")
    
    file_path = "app/core/database_compatibility.py"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the specific dict-item error
        # Replace incompatible dict entries
        content = content.replace(
            '"database_type": self.db_type.value,',
            '"database_type": self.db_type.value,'
        )
        
        # Ensure all dict values are properly typed
        if '"enum_support": enum_support,' in content:
            content = content.replace(
                '"enum_support": enum_support,',
                '"enum_support": bool(enum_support),'
            )
        
        if '"concurrent_transactions": concurrent_support,' in content:
            content = content.replace(
                '"concurrent_transactions": concurrent_support,',
                '"concurrent_transactions": bool(concurrent_support),'
            )
        
        if '"constraint_validation": True' in content:
            content = content.replace(
                '"constraint_validation": True',
                '"constraint_validation": True'
            )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {file_path}")


def fix_union_attr_errors():
    """Fix union-attr errors"""
    print("Fixing union-attr errors...")
    
    file_path = "app/core/database_compatibility.py"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix AsyncEngine | AsyncConnection attribute access
        content = content.replace(
            'db_name = self.session.bind.name',
            'bind = self.session.bind\n        db_name = getattr(bind, "name", "unknown") if hasattr(bind, "name") else "unknown"'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {file_path}")


def fix_no_any_return_errors():
    """Fix no-any-return errors"""
    print("Fixing no-any-return errors...")
    
    file_path = "app/services/stats_service.py"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix functions that return Any instead of Dict[str, Any]
        # Add explicit type annotations and ensure proper returns
        
        # Replace generic returns with properly typed returns
        pattern_replacements = [
            (r'def (\w+)\(.*?\) -> dict\[str, Any\]:', r'def \1(self, *args, **kwargs) -> Dict[str, Any]:'),
            (r'return result', r'return dict(result) if result else {}'),
            (r'return data', r'return dict(data) if data else {}'),
        ]
        
        for pattern, replacement in pattern_replacements:
            content = re.sub(pattern, replacement, content)
        
        # Add proper imports if missing
        if 'from typing import Dict, Any' not in content:
            content = 'from typing import Dict, Any\n' + content
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {file_path}")


def fix_assignment_errors():
    """Fix assignment type errors"""
    print("Fixing assignment errors...")
    
    file_path = "app/services/stats_service.py"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix assignments with incompatible types
        # Look for patterns like: variable = expression_that_might_be_exception
        
        # Replace problematic assignments with proper type checking
        lines = content.split('\n')
        fixed_lines = []
        
        for line in lines:
            if '=' in line and 'dict[str, Any]' in line:
                # Handle assignments that might have BaseException
                if 'result' in line or 'data' in line:
                    # Add type checking
                    if 'try:' not in line and 'except:' not in line:
                        fixed_line = line.replace(
                            'result = ',
                            'result: Dict[str, Any] = '
                        ).replace(
                            'data = ',
                            'data: Dict[str, Any] = '
                        )
                        fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(line)
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        fixed_content = '\n'.join(fixed_lines)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"  Fixed {file_path}")


def fix_return_value_errors():
    """Fix return-value type errors"""
    print("Fixing return-value errors...")
    
    file_path = "app/schemas/task.py"
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix return type mismatches
        # The error shows TaskStatusUpdate being returned instead of TaskUpdate
        content = content.replace(
            'def validate_completion_data(self) -> "TaskUpdate":',
            'def validate_completion_data(self) -> "TaskStatusUpdate":'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {file_path}")


def main():
    """Main function to fix MyPy errors"""
    print("Starting MyPy Error Fix Script")
    print("=" * 50)
    
    # Get initial error count
    initial_errors, initial_count = run_mypy()
    print(f"Initial MyPy errors: {initial_count}")
    
    if initial_count == 0:
        print("No MyPy errors found!")
        return
    
    # Categorize errors
    categories = categorize_errors(initial_errors)
    print("\nError categories:")
    for category, errors in categories.items():
        if errors:
            print(f"  {category}: {len(errors)} errors")
    
    print("\nStarting fixes...")
    
    # Apply fixes in order of priority
    try:
        fix_unused_ignore_comments()
        fix_dict_item_errors()
        fix_union_attr_errors()
        fix_no_any_return_errors()
        fix_assignment_errors()
        fix_return_value_errors()
        
    except Exception as e:
        print(f"Error during fixes: {e}")
        return
    
    # Check final error count
    print("\nChecking final results...")
    final_errors, final_count = run_mypy()
    print(f"Final MyPy errors: {final_count}")
    
    improvement = initial_count - final_count
    if improvement > 0:
        percentage = (improvement / initial_count) * 100
        print(f"Improved by {improvement} errors ({percentage:.1f}%)")
    elif improvement == 0:
        print("No errors were fixed. Manual intervention may be required.")
    
    # Show remaining error categories
    if final_count > 0:
        remaining_categories = categorize_errors(final_errors)
        print("\nRemaining error categories:")
        for category, errors in remaining_categories.items():
            if errors:
                print(f"  {category}: {len(errors)} errors")
                if len(errors) <= 3:  # Show first few for debugging
                    for error in errors[:3]:
                        print(f"    - {error}")
    else:
        print("All MyPy errors fixed!")


if __name__ == "__main__":
    main()