#!/usr/bin/env python3
"""
Script to fix Pydantic v2 compatibility issues in schemas.
Converts @validator and @root_validator to Pydantic v2 format.
"""

import re
import os

def fix_pydantic_v2_compatibility(file_path):
    """Fix Pydantic v2 compatibility issues in a file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix imports - add necessary v2 imports
    if 'from pydantic import' in content:
        content = re.sub(
            r'from pydantic import ([^,\n]+(?:,\s*[^,\n]+)*)',
            lambda m: f'from pydantic import {m.group(1).replace("validator, root_validator", "field_validator, model_validator, ConfigDict").replace("validator", "field_validator").replace("root_validator", "model_validator")}',
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
    
    # Fix root validator method body (values -> self)
    content = re.sub(
        r'(def \w+\(self\):\s*""".*?"""\s*)(.*?)(return values)',
        lambda m: m.group(1) + m.group(2).replace('values.get(', 'self.').replace('values', 'self') + 'return self',
        content,
        flags=re.DOTALL
    )
    
    # Fix class Config to model_config
    content = re.sub(
        r'(\s+)class Config:\s*\n(\s+)orm_mode = True',
        r'\1model_config = ConfigDict(from_attributes=True)',
        content,
        flags=re.MULTILINE
    )
    
    content = re.sub(
        r'(\s+)class Config:\s*\n(\s+)schema_extra = (\{.*?\})',
        r'\1model_config = ConfigDict(json_schema_extra=\3)',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix simple Config classes
    content = re.sub(
        r'(\s+)class Config:\s*\n(\s+)orm_mode = True\s*\n(\s+)schema_extra = (\{.*?\})',
        r'\1model_config = ConfigDict(from_attributes=True, json_schema_extra=\4)',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Write back the fixed content
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed Pydantic v2 compatibility issues in {file_path}")

if __name__ == "__main__":
    # Fix member.py
    member_file = "app/schemas/member.py"
    if os.path.exists(member_file):
        fix_pydantic_v2_compatibility(member_file)
    else:
        print(f"File {member_file} not found")