"""
数据导入服务
处理Excel文件导入、A/B表匹配、数据清洗和验证
"""

import logging
import os
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

import pandas as pd
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models.task import RepairTask, TaskType, TaskCategory, TaskPriority, TaskStatus
from app.models.member import Member
from app.core.config import settings, get_upload_path
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class ImportResult:
    """导入结果类"""
    def __init__(self):
        self.success = False
        self.total_rows = 0
        self.processed_rows = 0
        self.created_tasks = 0
        self.updated_tasks = 0
        self.skipped_rows = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.matched_data: List[Dict[str, Any]] = []
        self.unmatched_data: List[Dict[str, Any]] = []
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "summary": {
                "total_rows": self.total_rows,
                "processed_rows": self.processed_rows,
                "created_tasks": self.created_tasks,
                "updated_tasks": self.updated_tasks,
                "skipped_rows": self.skipped_rows
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "matched_count": len(self.matched_data),
            "unmatched_count": len(self.unmatched_data),
            "unmatched_data": self.unmatched_data[:10]  # 只返回前10条未匹配数据作为示例
        }


class DataImportService:
    """数据导入服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.task_service = TaskService(db)
        
        # A表和B表的列映射配置
        self.column_mappings = {
            # A表（维修任务表）可能的列名
            "task_table": {
                "task_id": ["任务编号", "工单编号", "task_id", "id"],
                "title": ["标题", "问题描述", "故障描述", "title", "description"],
                "reporter_name": ["报告人", "申请人", "报修人", "reporter", "applicant"],
                "reporter_contact": ["联系方式", "联系电话", "手机号", "电话", "contact", "phone"],
                "location": ["地点", "位置", "地址", "location", "address"],
                "report_time": ["报告时间", "申请时间", "报修时间", "创建时间", "report_time", "create_time"],
                "repair_type": ["维修类型", "故障类型", "repair_type", "type"],
                "priority": ["优先级", "紧急程度", "priority", "urgency"],
                "status": ["状态", "处理状态", "status"],
                "department": ["部门", "单位", "department", "unit"]
            },
            # B表（人员信息表）可能的列名
            "member_table": {
                "name": ["姓名", "报告人", "申请人", "name", "reporter"],
                "contact": ["联系方式", "联系电话", "手机号", "电话", "contact", "phone"],
                "email": ["邮箱", "电子邮件", "email"],
                "department": ["部门", "单位", "department", "unit"],
                "position": ["职位", "岗位", "position", "job_title"],
                "employee_id": ["工号", "员工编号", "employee_id", "id"]
            }
        }
    
    async def import_excel_file(self, file: UploadFile, import_options: Optional[Dict[str, Any]] = None) -> ImportResult:
        """
        导入Excel文件
        
        Args:
            file: 上传的Excel文件
            import_options: 导入选项配置
            
        Returns:
            ImportResult: 导入结果
        """
        result = ImportResult()
        temp_file_path = None
        
        try:
            logger.info(f"Starting Excel import: {file.filename}")
            
            # 验证文件类型
            if not self._validate_file_type(file.filename):
                result.errors.append("不支持的文件类型，请上传 .xlsx, .xls 或 .csv 文件")
                return result
            
            # 保存临时文件
            temp_file_path = await self._save_temp_file(file)
            
            # 解析Excel数据
            raw_data = await self._parse_excel_data(temp_file_path)
            result.total_rows = len(raw_data)
            
            if result.total_rows == 0:
                result.errors.append("文件中没有找到有效数据")
                return result
            
            # 检测数据表类型和结构
            table_info = self._detect_table_structure(raw_data)
            logger.info(f"Detected table structure: {table_info}")
            
            # 数据清洗和标准化
            cleaned_data = self._clean_and_normalize_data(raw_data, table_info)
            
            # A/B表匹配（如果需要）
            if import_options and import_options.get("enable_ab_matching", True):
                matched_data = await self._match_ab_tables(cleaned_data, table_info)
                result.matched_data = matched_data["matched"]
                result.unmatched_data = matched_data["unmatched"]
            else:
                result.matched_data = cleaned_data
            
            # 验证导入数据
            validation_result = self._validate_import_data(result.matched_data)
            result.errors.extend(validation_result["errors"])
            result.warnings.extend(validation_result["warnings"])
            
            if result.errors:
                logger.warning(f"Import validation failed: {result.errors}")
                return result
            
            # 创建任务
            if import_options and not import_options.get("dry_run", False):
                creation_result = await self._create_tasks_from_import(result.matched_data, import_options)
                result.created_tasks = creation_result["created"]
                result.updated_tasks = creation_result["updated"]
                result.skipped_rows = creation_result["skipped"]
            
            result.processed_rows = len(result.matched_data)
            result.success = True
            
            logger.info(f"Import completed successfully: {result.to_dict()}")
            return result
            
        except Exception as e:
            logger.error(f"Import failed: {str(e)}")
            result.errors.append(f"导入失败: {str(e)}")
            return result
            
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {str(e)}")
    
    async def _parse_excel_data(self, file_path: str) -> List[Dict[str, Any]]:
        """解析Excel数据"""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.csv':
                # 尝试不同的编码
                encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
                df = None
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                
                if df is None:
                    raise ValueError("无法解析CSV文件，请检查文件编码")
            
            else:  # Excel文件
                # 尝试读取第一个工作表
                df = pd.read_excel(file_path, sheet_name=0)
                
                # 如果第一个工作表为空，尝试其他工作表
                if df.empty:
                    excel_file = pd.ExcelFile(file_path)
                    for sheet_name in excel_file.sheet_names:
                        try:
                            df = pd.read_excel(file_path, sheet_name=sheet_name)
                            if not df.empty:
                                logger.info(f"Using sheet: {sheet_name}")
                                break
                        except Exception:
                            continue
            
            if df is None or df.empty:
                raise ValueError("文件中没有找到有效数据")
            
            # 清理列名（去除空格和特殊字符）
            df.columns = df.columns.astype(str).str.strip()
            
            # 删除完全为空的行
            df = df.dropna(how='all')
            
            # 转换为字典列表
            data = df.fillna('').to_dict('records')
            
            logger.info(f"Parsed {len(data)} rows from Excel file")
            return data
            
        except Exception as e:
            logger.error(f"Parse Excel error: {str(e)}")
            raise ValueError(f"解析Excel文件失败: {str(e)}")
    
    def _detect_table_structure(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测数据表结构"""
        if not data:
            return {"type": "unknown", "columns": []}
        
        columns = list(data[0].keys())
        
        # 分析列名，判断表类型
        task_score = 0
        member_score = 0
        
        for col in columns:
            col_lower = col.lower().strip()
            
            # 检查任务表特征
            task_keywords = ["任务", "工单", "故障", "维修", "报修", "问题", "task", "repair", "issue"]
            if any(keyword in col_lower for keyword in task_keywords):
                task_score += 2
            
            contact_keywords = ["联系", "电话", "手机", "contact", "phone"]
            if any(keyword in col_lower for keyword in contact_keywords):
                task_score += 1
                member_score += 1
            
            # 检查成员表特征
            member_keywords = ["姓名", "员工", "人员", "name", "employee", "staff"]
            if any(keyword in col_lower for keyword in member_keywords):
                member_score += 2
            
            dept_keywords = ["部门", "单位", "department", "unit"]
            if any(keyword in col_lower for keyword in dept_keywords):
                member_score += 1
        
        # 判断表类型
        if task_score > member_score:
            table_type = "task_table"
        elif member_score > task_score:
            table_type = "member_table"
        else:
            table_type = "mixed_table"  # 可能包含任务和人员信息
        
        return {
            "type": table_type,
            "columns": columns,
            "task_score": task_score,
            "member_score": member_score,
            "total_rows": len(data)
        }
    
    def _clean_and_normalize_data(self, data: List[Dict[str, Any]], table_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """清洗和标准化数据"""
        cleaned_data = []
        
        for row_idx, row in enumerate(data):
            try:
                cleaned_row = {}
                
                for original_col, value in row.items():
                    # 清理列名
                    clean_col = str(original_col).strip()
                    
                    # 清理数据值
                    if pd.isna(value) or value == '' or str(value).strip() == '':
                        clean_value = None
                    else:
                        clean_value = str(value).strip()
                        
                        # 特殊处理联系方式（去除非数字字符，保留数字和+号）
                        if any(keyword in clean_col.lower() for keyword in ["联系", "电话", "手机", "contact", "phone"]):
                            clean_value = self._clean_contact_info(clean_value)
                        
                        # 特殊处理时间字段
                        elif any(keyword in clean_col.lower() for keyword in ["时间", "日期", "time", "date"]):
                            clean_value = self._clean_datetime(clean_value)
                    
                    cleaned_row[clean_col] = clean_value
                
                # 只保留至少有一个非空字段的行
                if any(v for v in cleaned_row.values() if v is not None):
                    cleaned_data.append(cleaned_row)
                
            except Exception as e:
                logger.warning(f"Error cleaning row {row_idx}: {str(e)}")
                continue
        
        logger.info(f"Cleaned data: {len(cleaned_data)} valid rows")
        return cleaned_data
    
    def _clean_contact_info(self, contact: str) -> str:
        """清理联系方式"""
        if not contact:
            return ""
        
        # 移除常见的格式字符，保留数字、+、-、空格
        import re
        cleaned = re.sub(r'[^\d+\-\s]', '', contact)
        cleaned = re.sub(r'\s+', '', cleaned)  # 移除空格
        
        # 如果是手机号，标准化格式
        if len(cleaned) == 11 and cleaned.startswith('1'):
            return cleaned
        elif len(cleaned) == 13 and cleaned.startswith('+86'):
            return cleaned[3:]  # 去掉+86前缀
        
        return cleaned
    
    def _clean_datetime(self, datetime_str: str) -> Optional[str]:
        """清理时间字段"""
        if not datetime_str:
            return None
        
        try:
            # 尝试解析各种时间格式
            from dateutil import parser
            dt = parser.parse(datetime_str)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            # 如果解析失败，返回原字符串
            return datetime_str
    
    async def _match_ab_tables(self, data: List[Dict[str, Any]], table_info: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """A/B表匹配算法"""
        logger.info("Starting A/B table matching...")
        
        matched_data = []
        unmatched_data = []
        
        # 获取现有成员数据用于匹配
        member_query = select(Member).where(Member.is_active == True)
        member_result = await self.db.execute(member_query)
        existing_members = {
            self._create_match_key(m.name, m.phone): m 
            for m in member_result.scalars().all()
            if m.name and m.phone
        }
        
        logger.info(f"Found {len(existing_members)} existing members for matching")
        
        for row in data:
            try:
                # 提取姓名和联系方式
                name = self._extract_field_value(row, "reporter_name", table_info)
                contact = self._extract_field_value(row, "reporter_contact", table_info)
                
                if not name or not contact:
                    unmatched_data.append({
                        **row,
                        "_match_reason": "缺少姓名或联系方式"
                    })
                    continue
                
                # 创建匹配键
                match_key = self._create_match_key(name, contact)
                
                # 尝试精确匹配
                matched_member = existing_members.get(match_key)
                
                # 如果精确匹配失败，尝试模糊匹配
                if not matched_member:
                    matched_member = self._fuzzy_match_member(name, contact, existing_members)
                
                if matched_member:
                    # 匹配成功，创建标准化的任务数据
                    task_data = self._create_standardized_task_data(row, matched_member, table_info)
                    matched_data.append(task_data)
                else:
                    unmatched_data.append({
                        **row,
                        "_match_reason": f"未找到匹配的成员: {name} ({contact})"
                    })
                
            except Exception as e:
                logger.warning(f"Error matching row: {str(e)}")
                unmatched_data.append({
                    **row,
                    "_match_reason": f"匹配过程出错: {str(e)}"
                })
        
        logger.info(f"Matching completed: {len(matched_data)} matched, {len(unmatched_data)} unmatched")
        
        return {
            "matched": matched_data,
            "unmatched": unmatched_data
        }
    
    def _extract_field_value(self, row: Dict[str, Any], field_type: str, table_info: Dict[str, Any]) -> Optional[str]:
        """从行数据中提取指定字段的值"""
        table_type = table_info["type"]
        possible_columns = self.column_mappings.get(table_type, {}).get(field_type, [])
        
        for col_name in row.keys():
            col_lower = col_name.lower().strip()
            
            # 检查是否匹配预定义的列名
            for possible_col in possible_columns:
                if possible_col.lower() in col_lower or col_lower in possible_col.lower():
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
    
    def _create_match_key(self, name: str, contact: str) -> str:
        """创建用于匹配的键"""
        if not name or not contact:
            return ""
        
        # 标准化姓名（去除空格和特殊字符）
        clean_name = ''.join(name.split())
        
        # 标准化联系方式（只保留数字）
        clean_contact = ''.join(filter(str.isdigit, contact))
        
        return f"{clean_name}:{clean_contact}"
    
    def _fuzzy_match_member(self, name: str, contact: str, existing_members: Dict[str, Member]) -> Optional[Member]:
        """模糊匹配成员"""
        # 简单的模糊匹配逻辑
        clean_name = ''.join(name.split())
        clean_contact = ''.join(filter(str.isdigit, contact))
        
        for key, member in existing_members.items():
            stored_name, stored_contact = key.split(':')
            
            # 姓名相似度匹配（简单的字符串包含）
            name_match = (clean_name in stored_name or stored_name in clean_name)
            
            # 联系方式匹配（后8位相同认为是同一人）
            if len(clean_contact) >= 8 and len(stored_contact) >= 8:
                contact_match = clean_contact[-8:] == stored_contact[-8:]
            else:
                contact_match = clean_contact == stored_contact
            
            if name_match and contact_match:
                return member
        
        return None
    
    def _create_standardized_task_data(self, row: Dict[str, Any], member: Member, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """创建标准化的任务数据"""
        # 提取各个字段
        title = self._extract_field_value(row, "title", table_info) or "导入的维修任务"
        location = self._extract_field_value(row, "location", table_info)
        report_time_str = self._extract_field_value(row, "report_time", table_info)
        repair_type = self._extract_field_value(row, "repair_type", table_info)
        
        # 解析报告时间
        report_time = datetime.utcnow()
        if report_time_str:
            try:
                from dateutil import parser
                report_time = parser.parse(report_time_str)
            except Exception:
                pass
        
        # 判断任务类型
        task_type = TaskType.ONLINE
        if repair_type:
            offline_keywords = ["现场", "上门", "实地", "offline", "onsite"]
            if any(keyword in repair_type.lower() for keyword in offline_keywords):
                task_type = TaskType.OFFLINE
        
        # 判断任务类别
        category = TaskCategory.NETWORK_REPAIR
        if repair_type:
            if "网络" in repair_type or "network" in repair_type.lower():
                category = TaskCategory.NETWORK_REPAIR
            elif "设备" in repair_type or "硬件" in repair_type or "equipment" in repair_type.lower():
                category = TaskCategory.EQUIPMENT_REPAIR
            elif "软件" in repair_type or "系统" in repair_type or "software" in repair_type.lower():
                category = TaskCategory.SOFTWARE_REPAIR
        
        return {
            "title": title,
            "description": f"从Excel导入的任务。原始数据: {str(row)[:200]}",
            "category": category,
            "priority": TaskPriority.MEDIUM,
            "task_type": task_type,
            "location": location,
            "assigned_to": member.id,
            "reporter_name": member.name,
            "reporter_contact": member.phone,
            "report_time": report_time,
            "_original_data": row,
            "_matched_member": {
                "id": member.id,
                "name": member.name,
                "phone": member.phone,
                "email": member.email
            }
        }
    
    def _validate_import_data(self, data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """验证导入数据"""
        errors = []
        warnings = []
        
        if not data:
            errors.append("没有有效的数据可导入")
            return {"errors": errors, "warnings": warnings}
        
        # 检查必需字段
        required_fields = ["title", "reporter_name", "reporter_contact"]
        
        for idx, row in enumerate(data):
            row_errors = []
            
            for field in required_fields:
                if not row.get(field):
                    row_errors.append(f"缺少必需字段: {field}")
            
            # 验证联系方式格式
            contact = row.get("reporter_contact")
            if contact and not self._is_valid_contact(contact):
                warnings.append(f"第{idx+1}行联系方式格式可能不正确: {contact}")
            
            if row_errors:
                errors.append(f"第{idx+1}行数据错误: {', '.join(row_errors)}")
        
        return {"errors": errors, "warnings": warnings}
    
    def _is_valid_contact(self, contact: str) -> bool:
        """验证联系方式格式"""
        if not contact:
            return False
        
        # 简单的手机号验证
        digits = ''.join(filter(str.isdigit, contact))
        return len(digits) >= 10  # 至少10位数字
    
    async def _create_tasks_from_import(self, validated_data: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, int]:
        """从导入数据创建任务"""
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        creator_id = options.get("creator_id", 1)  # 默认创建者ID
        
        for row in validated_data:
            try:
                # 检查是否已存在相同的任务（基于标题和报告人）
                existing_query = select(RepairTask).where(
                    and_(
                        RepairTask.title == row["title"],
                        RepairTask.reporter_name == row["reporter_name"],
                        RepairTask.reporter_contact == row["reporter_contact"]
                    )
                )
                existing_result = await self.db.execute(existing_query)
                existing_task = existing_result.scalar_one_or_none()
                
                if existing_task:
                    if options.get("update_existing", False):
                        # 更新现有任务
                        if row.get("location"):
                            existing_task.location = row["location"]
                        if row.get("description"):
                            existing_task.description = row["description"]
                        
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    # 创建新任务
                    task = await self.task_service.create_repair_task(row, creator_id)
                    created_count += 1
                
            except Exception as e:
                logger.error(f"Error creating task from import data: {str(e)}")
                skipped_count += 1
        
        await self.db.commit()
        
        return {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count
        }
    
    async def _save_temp_file(self, file: UploadFile) -> str:
        """保存临时文件"""
        # 创建临时文件
        suffix = Path(file.filename).suffix if file.filename else '.xlsx'
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=get_upload_path())
        
        try:
            # 写入文件内容
            with os.fdopen(temp_fd, 'wb') as temp_file:
                content = await file.read()
                temp_file.write(content)
            
            return temp_path
            
        except Exception as e:
            # 清理文件描述符
            try:
                os.close(temp_fd)
            except:
                pass
            raise e
    
    def _validate_file_type(self, filename: Optional[str]) -> bool:
        """验证文件类型"""
        if not filename:
            return False
        
        allowed_extensions = ['.xlsx', '.xls', '.csv']
        file_ext = Path(filename).suffix.lower()
        return file_ext in allowed_extensions
    
    async def get_import_template(self, template_type: str = "repair_task") -> Dict[str, Any]:
        """获取导入模板"""
        templates = {
            "repair_task": {
                "filename": "repair_task_template.xlsx",
                "columns": [
                    {"name": "标题", "field": "title", "required": True, "example": "网络故障"},
                    {"name": "报告人", "field": "reporter_name", "required": True, "example": "张三"},
                    {"name": "联系方式", "field": "reporter_contact", "required": True, "example": "13800138000"},
                    {"name": "地点", "field": "location", "required": False, "example": "办公楼A座201"},
                    {"name": "故障描述", "field": "description", "required": False, "example": "无法连接网络"},
                    {"name": "维修类型", "field": "repair_type", "required": False, "example": "网络维修"},
                    {"name": "报告时间", "field": "report_time", "required": False, "example": "2024-01-20 10:30:00"},
                    {"name": "优先级", "field": "priority", "required": False, "example": "中等"}
                ]
            }
        }
        
        return templates.get(template_type, {})
    
    async def preview_import_data(self, file: UploadFile, preview_rows: int = 10) -> Dict[str, Any]:
        """预览导入数据"""
        temp_file_path = None
        
        try:
            # 保存临时文件
            temp_file_path = await self._save_temp_file(file)
            
            # 解析数据
            raw_data = await self._parse_excel_data(temp_file_path)
            
            # 检测表结构
            table_info = self._detect_table_structure(raw_data)
            
            # 返回预览数据
            preview_data = raw_data[:preview_rows]
            
            return {
                "success": True,
                "table_info": table_info,
                "preview_data": preview_data,
                "total_rows": len(raw_data),
                "preview_rows": len(preview_data)
            }
            
        except Exception as e:
            logger.error(f"Preview import data error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {str(e)}")