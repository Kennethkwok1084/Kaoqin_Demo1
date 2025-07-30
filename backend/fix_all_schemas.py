#!/usr/bin/env python3
"""
Comprehensive script to fix all Pydantic v2 compatibility issues in schema files.
"""

import re
import os
import glob

def fix_pydantic_v2_comprehensive(file_path):
    """Fix all Pydantic v2 compatibility issues in a file."""
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports - update to v2 imports
    content = re.sub(
        r'from pydantic import ([^,\n]+(?:,\s*[^,\n]+)*)',
        lambda m: f'from pydantic import {m.group(1).replace("validator, root_validator", "field_validator, model_validator, ConfigDict").replace("validator", "field_validator").replace("root_validator", "model_validator").replace("field_field_validator", "field_validator").replace("model_field_validator", "model_validator")}',
        content
    )
    
    # Ensure ConfigDict is imported if Config classes exist
    if 'class Config:' in content and 'ConfigDict' not in content:
        content = re.sub(
            r'from pydantic import ([^,\n]+(?:,\s*[^,\n]+)*)',
            lambda m: f'from pydantic import {m.group(1)}, ConfigDict' if 'ConfigDict' not in m.group(1) else m.group(0),
            content
        )
    
    # Fix @validator to @field_validator with @classmethod
    content = re.sub(
        r'(\s+)@validator\((.*?)\)\s*\n(\s+)def (\w+)\(cls, v\):',
        r'\1@field_validator(\2)\n\1@classmethod\n\3def \4(cls, v):',
        content,
        flags=re.MULTILINE
    )
    
    # Fix @root_validator to @model_validator(mode='after')
    content = re.sub(
        r'(\s+)@root_validator\s*\n(\s+)def (\w+)\(cls, values\):',
        r'\1@model_validator(mode=\'after\')\n\2def \3(self):',
        content,
        flags=re.MULTILINE
    )
    
    # Fix root validator method body (values.get() -> self.)
    def fix_root_validator_body(match):
        indent = match.group(1)
        method_name = match.group(2)
        docstring = match.group(3) if match.group(3) else ""
        body = match.group(4)
        
        # Replace values.get('field') with self.field
        body = re.sub(r"values\.get\('(\w+)'\)", r"self.\1", body)
        body = re.sub(r"values\.get\(\"(\w+)\"\)", r"self.\1", body)
        body = re.sub(r"values\[['\"]\w+['\"]\]", lambda m: m.group(0).replace("values", "self"), body)
        
        # Replace return values with return self
        body = re.sub(r'return values\b', 'return self', body)
        
        return f"{indent}def {method_name}(self):{docstring}{body}"
    
    content = re.sub(
        r'(\s+)def (\w+)\(self\):(\s*""".*?""")?(\s*.*?return self)',
        fix_root_validator_body,
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix regex to pattern in Field
    content = re.sub(r'\bregex=', 'pattern=', content)
    
    # Fix class Config: orm_mode = True
    content = re.sub(
        r'(\s+)class Config:\s*\n(\s+)orm_mode = True\s*(?:\n|$)',
        r'\1model_config = ConfigDict(from_attributes=True)\n',
        content,
        flags=re.MULTILINE
    )
    
    # Fix class Config: schema_extra = {...}
    def fix_schema_extra(match):
        indent = match.group(1)
        schema_content = match.group(2)
        return f"{indent}model_config = ConfigDict(json_schema_extra={schema_content})\n"
    
    content = re.sub(
        r'(\s+)class Config:\s*\n\s+schema_extra = (\{.*?\})',
        fix_schema_extra,
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix class Config with both orm_mode and schema_extra
    def fix_combined_config(match):
        indent = match.group(1)
        schema_content = match.group(2)
        return f"{indent}model_config = ConfigDict(from_attributes=True, json_schema_extra={schema_content})\n"
    
    content = re.sub(
        r'(\s+)class Config:\s*\n\s+orm_mode = True\s*\n\s+schema_extra = (\{.*?\})',
        fix_combined_config,
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Remove any remaining empty Config classes
    content = re.sub(
        r'(\s+)class Config:\s*\n(?=\s*\n|\s*class|\s*def|\Z)',
        '',
        content,
        flags=re.MULTILINE
    )
    
    # Fix min_items/max_items to min_length/max_length for List fields
    content = re.sub(r'\bmin_items=', 'min_length=', content)
    content = re.sub(r'\bmax_items=', 'max_length=', content)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  Fixed {file_path}")
    else:
        print(f"  No changes needed in {file_path}")

def main():
    """Fix all schema files in the project."""
    schema_files = glob.glob("app/schemas/*.py")
    
    for file_path in schema_files:
        if file_path.endswith('__init__.py'):
            continue
        fix_pydantic_v2_comprehensive(file_path)
    
    print("\nAll schema files have been processed!")

if __name__ == "__main__":
    main()