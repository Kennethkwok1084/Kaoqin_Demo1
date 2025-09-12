#!/usr/bin/env python3
"""
Excel导入名字匹配调试脚本
用于分析为什么Excel导入时名字匹配不上
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional
import pandas as pd

# 添加后端路径到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.database import get_db
from backend.app.models.member import Member
from sqlalchemy import select


class ImportMatchingDebugger:
    """导入匹配调试器"""
    
    def __init__(self):
        self.column_mappings = {
            "A表": {
                "reporter_name": [
                    "报告人", "申请人", "报修人", "reporter", "applicant", "联系人", "申请者",
                ],
                "reporter_contact": [
                    "联系方式", "电话", "手机", "contact", "phone", "联系电话", "手机号",
                ],
            }
        }
    
    def _create_match_key(self, name: str, contact: str) -> str:
        """创建用于匹配的键（与import_service.py中的逻辑完全一致）"""
        if not name or not contact:
            return ""
        
        # 标准化姓名（去除空格和特殊字符）
        clean_name = "".join(name.split())
        
        # 标准化联系方式（只保留数字）
        clean_contact = "".join(filter(str.isdigit, contact))
        
        return f"{clean_name}:{clean_contact}"
    
    def _extract_field_value(self, row: Dict[str, Any], field_type: str) -> Optional[str]:
        """从行数据中提取指定字段的值"""
        possible_columns = self.column_mappings.get("A表", {}).get(field_type, [])
        
        for col_name in row.keys():
            col_lower = col_name.lower().strip()
            
            # 检查是否匹配预定义的列名
            for possible_col in possible_columns:
                if (
                    possible_col.lower() in col_lower
                    or col_lower in possible_col.lower()
                ):
                    value = row[col_name]
                    if value and str(value).strip():
                        return str(value).strip()
            
            # 检查列名中是否包含关键词
            if field_type == "reporter_name":
                name_keywords = ["姓名", "报告", "申请", "报修", "name", "reporter"]
                if any(keyword in col_lower for keyword in name_keywords):
                    value = row[col_name]
                    if value and str(value).strip():
                        return str(value).strip()
            
            elif field_type == "reporter_contact":
                contact_keywords = ["联系", "电话", "手机", "contact", "phone"]
                if any(keyword in col_lower for keyword in contact_keywords):
                    value = row[col_name]
                    if value and str(value).strip():
                        return str(value).strip()
        
        return None
    
    async def debug_excel_file(self, excel_file_path: str, max_rows: int = 10):
        """调试Excel文件的匹配情况"""
        print(f"🔍 调试Excel文件: {excel_file_path}")
        print("=" * 80)
        
        # 1. 读取Excel文件
        try:
            df = pd.read_excel(excel_file_path)
            print(f"✅ Excel文件读取成功，共 {len(df)} 行数据")
            print(f"📋 列名: {list(df.columns)}")
            print()
        except Exception as e:
            print(f"❌ Excel文件读取失败: {e}")
            return
        
        # 2. 获取数据库中的现有成员
        print("🔍 获取数据库中的现有成员...")
        try:
            async for db in get_db():
                member_query = select(Member).where(Member.is_active)
                member_result = await db.execute(member_query)
                existing_members = {
                    self._create_match_key(m.name, getattr(m, "phone", "")): m
                    for m in member_result.scalars().all()
                    if m.name and hasattr(m, "phone") and m.phone
                }
                break
            
            print(f"✅ 找到 {len(existing_members)} 个活跃成员")
            print(f"📋 成员匹配键示例: {list(existing_members.keys())[:5]}")
            print()
        except Exception as e:
            print(f"❌ 获取数据库成员失败: {e}")
            return
        
        # 3. 分析每行数据的匹配情况
        print("🔍 分析每行数据的匹配情况...")
        print("-" * 80)
        
        for idx, row in df.head(max_rows).iterrows():
            print(f"\n第 {idx + 1} 行数据:")
            row_dict = row.to_dict()
            
            # 提取姓名和联系方式
            name = self._extract_field_value(row_dict, "reporter_name")
            contact = self._extract_field_value(row_dict, "reporter_contact")
            
            print(f"  原始数据: {dict(row_dict)}")
            print(f"  提取姓名: '{name}'")
            print(f"  提取联系方式: '{contact}'")
            
            if not name:
                print(f"  ❌ 无法提取姓名 - 可能的列名不匹配")
                self._suggest_name_columns(row_dict)
                continue
            
            if not contact:
                print(f"  ❌ 无法提取联系方式 - 可能的列名不匹配")
                self._suggest_contact_columns(row_dict)
                continue
            
            # 创建匹配键
            match_key = self._create_match_key(name, contact)
            print(f"  生成匹配键: '{match_key}'")
            
            # 尝试匹配
            matched_member = existing_members.get(match_key)
            if matched_member:
                print(f"  ✅ 匹配成功: {matched_member.name} ({matched_member.phone})")
            else:
                print(f"  ❌ 匹配失败")
                self._suggest_similar_matches(match_key, existing_members)
        
        print("\n" + "=" * 80)
        print("调试完成")
    
    def _suggest_name_columns(self, row_dict: Dict[str, Any]):
        """建议可能的姓名列"""
        possible_name_cols = []
        for col_name, value in row_dict.items():
            if value and isinstance(value, str) and len(value.strip()) <= 10:
                col_lower = col_name.lower()
                if any(keyword in col_lower for keyword in ["名", "name", "人", "者"]):
                    possible_name_cols.append(col_name)
        
        if possible_name_cols:
            print(f"    💡 可能的姓名列: {possible_name_cols}")
    
    def _suggest_contact_columns(self, row_dict: Dict[str, Any]):
        """建议可能的联系方式列"""
        possible_contact_cols = []
        for col_name, value in row_dict.items():
            if value:
                col_lower = col_name.lower()
                if any(keyword in col_lower for keyword in ["联系", "电话", "手机", "phone", "contact"]):
                    possible_contact_cols.append(col_name)
                # 检查是否像手机号
                elif isinstance(value, (str, int)) and str(value).isdigit() and len(str(value)) >= 8:
                    possible_contact_cols.append(col_name)
        
        if possible_contact_cols:
            print(f"    💡 可能的联系方式列: {possible_contact_cols}")
    
    def _suggest_similar_matches(self, target_key: str, existing_members: Dict[str, Any]):
        """建议相似的匹配"""
        target_name, target_contact = target_key.split(":")
        similar_matches = []
        
        for key, member in existing_members.items():
            stored_name, stored_contact = key.split(":")
            
            # 检查姓名相似性
            name_similar = (
                target_name in stored_name or 
                stored_name in target_name or
                target_name == stored_name
            )
            
            # 检查联系方式相似性
            contact_similar = False
            if len(target_contact) >= 8 and len(stored_contact) >= 8:
                contact_similar = target_contact[-8:] == stored_contact[-8:]
            else:
                contact_similar = target_contact == stored_contact
            
            if name_similar or contact_similar:
                similar_matches.append((key, member, name_similar, contact_similar))
        
        if similar_matches:
            print(f"    💡 相似匹配:")
            for key, member, name_match, contact_match in similar_matches[:3]:
                match_type = []
                if name_match:
                    match_type.append("姓名")
                if contact_match:
                    match_type.append("联系方式")
                print(f"      - {member.name} ({member.phone}) [匹配: {', '.join(match_type)}]")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python debug_import_matching.py <excel_file_path> [max_rows]")
        print("示例: python debug_import_matching.py /path/to/your/excel.xlsx 5")
        return
    
    excel_file_path = sys.argv[1]
    max_rows = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    if not os.path.exists(excel_file_path):
        print(f"❌ Excel文件不存在: {excel_file_path}")
        return
    
    debugger = ImportMatchingDebugger()
    await debugger.debug_excel_file(excel_file_path, max_rows)


if __name__ == "__main__":
    asyncio.run(main())
