"""
A/B表智能匹配服务（重构版）
实现高精度的A/B表匹配算法，目标匹配率 > 95%
支持多种匹配策略和机器学习优化
"""

import asyncio
import hashlib
import logging
import re
import time
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member

logger = logging.getLogger(__name__)


class MatchingStrategy(Enum):
    """匹配策略枚举"""

    EXACT = "exact"  # 精确匹配
    FUZZY = "fuzzy"  # 模糊匹配
    PHONETIC = "phonetic"  # 音似匹配
    MULTI_FIELD = "multi_field"  # 多字段组合匹配
    LEARNING = "learning"  # 机器学习匹配


class MatchConfidence(Enum):
    """匹配置信度等级"""

    HIGH = "high"  # 高置信度 (90-100%)
    MEDIUM = "medium"  # 中等置信度 (70-89%)
    LOW = "low"  # 低置信度 (50-69%)
    VERY_LOW = "very_low"  # 极低置信度 (<50%)


@dataclass
class MatchResult:
    """匹配结果数据类"""

    a_record: Dict[str, Any]  # A表记录
    b_record: Optional[Dict[str, Any]]  # B表匹配记录
    member: Optional[Member]  # 匹配到的成员
    confidence: float  # 匹配置信度 (0-1)
    confidence_level: MatchConfidence  # 置信度等级
    strategy_used: MatchingStrategy  # 使用的匹配策略
    match_details: Dict[str, Any]  # 详细匹配信息
    is_matched: bool  # 是否匹配成功
    failure_reason: Optional[str]  # 匹配失败原因


class ABTableMatchingService:
    """A/B表智能匹配服务"""

    def __init__(self, db: Optional[AsyncSession]):
        if db is None:
            raise ValueError("Database session is required")
        self.db = db

        # 匹配权重配置
        self.field_weights = {
            "name": 0.4,  # 姓名权重40%
            "phone": 0.35,  # 电话权重35%
            "email": 0.15,  # 邮箱权重15%
            "department": 0.1,  # 部门权重10%
        }

        # 模糊匹配阈值
        self.thresholds = {
            "high_confidence": 0.90,
            "medium_confidence": 0.70,
            "low_confidence": 0.50,
            "min_acceptable": 0.30,
        }

        # 预编译正则表达式
        self._phone_clean_pattern = re.compile(r"[^\d+]")
        self._name_clean_pattern = re.compile(
            r"[^\u4e00-\u9fff\u0041-\u005a\u0061-\u007a·]"
        )

        # 优化缓存系统
        self._similarity_cache = {}
        self._phone_cache = {}
        self._name_cache = {}
        self._cache_hits = 0
        self._cache_misses = 0

    async def match_ab_tables(
        self,
        a_table_data: List[Dict[str, Any]],
        b_table_data: Optional[List[Dict[str, Any]]] = None,
        strategies: Optional[List[MatchingStrategy]] = None,
        batch_size: int = 100,
        timeout_seconds: int = 240,  # 4 minutes timeout
    ) -> List[MatchResult]:
        """
        执行A/B表智能匹配

        Args:
            a_table_data: A表数据（维修任务数据）
            b_table_data: B表数据（成员信息数据）
            strategies: 使用的匹配策略列表

        Returns:
            List[MatchResult]: 匹配结果列表
        """
        if strategies is None:
            strategies = [
                MatchingStrategy.EXACT,
                MatchingStrategy.FUZZY,
                MatchingStrategy.MULTI_FIELD,
            ]

        try:
            start_time = time.time()
            logger.info(
                f"Starting AB table matching with {
                    len(a_table_data)} A-records, timeout: {timeout_seconds}s"
            )

            # 获取现有成员数据
            members = await self._get_all_active_members()
            member_index = self._build_member_index(members)

            # 如果提供了B表数据，合并到成员索引中
            if b_table_data:
                member_index = self._merge_b_table_data(member_index, b_table_data)

            # 执行批量匹配
            match_results: List[MatchResult] = []
            total_records = len(a_table_data)

            for i in range(0, total_records, batch_size):
                batch = a_table_data[i : i + batch_size]
                batch_end = min(i + batch_size, total_records)

                logger.info(
                    f"Processing batch {i // batch_size + 1}: records "
                    f"{i + 1}-{batch_end}/{total_records}"
                )

                # Process batch
                for j, a_record in enumerate(batch):
                    # Check timeout
                    if time.time() - start_time > timeout_seconds:
                        logger.warning(
                            f"AB table matching timeout after {timeout_seconds}s, "
                            f"processed {len(match_results)}/{total_records} records"
                        )
                        # Return partial results instead of failing completely
                        stats = self._calculate_matching_stats(match_results)
                        logger.info(
                            f"Partial matching completed due to timeout: {stats}"
                        )
                        return match_results

                    result = await self._match_single_record(
                        a_record, member_index, strategies
                    )
                    match_results.append(result)

                    # Log progress every 50 records
                    if (i + j + 1) % 50 == 0:
                        progress = (i + j + 1) / total_records * 100
                        elapsed_time = time.time() - start_time
                        estimated_total_time = (
                            elapsed_time / progress * 100 if progress > 0 else 0
                        )
                        logger.info(
                            f"Progress: {progress:.1f}% "
                            f"({i + j + 1}/{total_records} records), "
                            f"elapsed: {elapsed_time:.1f}s, "
                            f"estimated total: {estimated_total_time:.1f}s"
                        )

                # Small pause between batches to prevent overwhelming the database
                await asyncio.sleep(0.01)  # 10ms pause

            # 统计结果
            stats = self._calculate_matching_stats(match_results)

            # 缓存性能统计
            cache_stats = {
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": self._cache_hits
                / max(self._cache_hits + self._cache_misses, 1),
            }

            logger.info(f"Matching completed: {stats}")
            logger.info(f"Cache performance: {cache_stats}")

            return match_results

        except Exception as e:
            logger.error(f"AB table matching error: {str(e)}")
            raise

    async def _match_single_record(
        self,
        a_record: Dict[str, Any],
        member_index: Dict[str, Any],
        strategies: List[MatchingStrategy],
    ) -> MatchResult:
        """匹配单条A表记录"""
        try:
            # 提取关键字段
            name = self._extract_name(a_record)
            phone = self._extract_phone(a_record)
            email = self._extract_email(a_record)

            if not name and not phone:
                return MatchResult(
                    a_record=a_record,
                    b_record=None,
                    member=None,
                    confidence=0.0,
                    confidence_level=MatchConfidence.VERY_LOW,
                    strategy_used=MatchingStrategy.EXACT,
                    match_details={"error": "缺少姓名和电话信息"},
                    is_matched=False,
                    failure_reason="缺少必要的匹配字段",
                )

            # 按策略优先级依次尝试匹配
            best_match = None
            best_confidence = 0.0

            for strategy in strategies:
                candidates = await self._find_candidates_by_strategy(
                    name, phone, email, member_index, strategy
                )

                for candidate in candidates:
                    confidence = self._calculate_match_confidence(
                        {"name": name, "phone": phone, "email": email},
                        candidate,
                        strategy,
                    )

                    if confidence > best_confidence:
                        best_confidence = confidence
                        best_match = candidate
                        best_strategy = strategy

                        # 如果找到高置信度匹配，提前结束
                        if confidence >= self.thresholds["high_confidence"]:
                            break

                if best_confidence >= self.thresholds["high_confidence"]:
                    break

            # 构建匹配结果
            if best_match and best_confidence >= self.thresholds["min_acceptable"]:
                confidence_level = self._get_confidence_level(best_confidence)

                return MatchResult(
                    a_record=a_record,
                    b_record=best_match.get("b_data"),
                    member=best_match["member"],
                    confidence=best_confidence,
                    confidence_level=confidence_level,
                    strategy_used=best_strategy,
                    match_details=self._build_match_details(
                        {"name": name, "phone": phone, "email": email},
                        best_match,
                        best_confidence,
                    ),
                    is_matched=True,
                    failure_reason=None,
                )
            else:
                return MatchResult(
                    a_record=a_record,
                    b_record=None,
                    member=None,
                    confidence=best_confidence,
                    confidence_level=MatchConfidence.VERY_LOW,
                    strategy_used=(
                        strategies[0] if strategies else MatchingStrategy.EXACT
                    ),
                    match_details={
                        "searched_candidates": len(member_index.get("by_name", {}))
                    },
                    is_matched=False,
                    failure_reason=f"未找到足够置信度的匹配（最高置信度: {best_confidence:.2f}）",
                )

        except Exception as e:
            logger.error(f"Single record matching error: {str(e)}")
            return MatchResult(
                a_record=a_record,
                b_record=None,
                member=None,
                confidence=0.0,
                confidence_level=MatchConfidence.VERY_LOW,
                strategy_used=MatchingStrategy.EXACT,
                match_details={"error": str(e)},
                is_matched=False,
                failure_reason=f"匹配过程出错: {str(e)}",
            )

    async def _get_all_active_members(self) -> List[Member]:
        """获取所有活跃成员"""
        query = select(Member).where(Member.is_active)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    def _build_member_index(self, members: List[Member]) -> Dict[str, Any]:
        """构建成员索引以提高匹配效率（优化版）"""
        index: Dict[str, Dict[str, Any]] = {
            "by_name": {},  # 按姓名索引
            "by_phone": {},  # 按电话索引
            "by_email": {},  # 按邮箱索引
            "by_name_phone": {},  # 按姓名+电话组合索引
            "by_phone_suffix": {},  # 按电话后缀索引（快速查找）
            "fuzzy_name_groups": {},  # 按姓名首字符分组（模糊匹配优化）
        }

        for member in members:
            member_data = {
                "member": member,
                "b_data": None,  # B表数据（如果有）
                "clean_name": self._clean_name(member.name),
                "clean_phone": self._clean_phone(getattr(member, "phone", "")),
                "email": (
                    getattr(member, "email", "").lower()
                    if hasattr(member, "email")
                    else ""
                ),
                "department": getattr(member, "department", ""),
                "student_id": getattr(member, "student_id", ""),
            }

            # 姓名索引
            clean_name = member_data["clean_name"]
            if clean_name:
                name_key = str(clean_name)
                if name_key not in index["by_name"]:
                    index["by_name"][name_key] = []
                index["by_name"][name_key].append(member_data)

            # 电话索引
            clean_phone = member_data["clean_phone"]
            if clean_phone:
                phone_key = str(clean_phone)
                if phone_key not in index["by_phone"]:
                    index["by_phone"][phone_key] = []
                index["by_phone"][phone_key].append(member_data)

            # 邮箱索引
            email = member_data["email"]
            if email:
                email_key = str(email)
                if email_key not in index["by_email"]:
                    index["by_email"][email_key] = []
                index["by_email"][email_key].append(member_data)

            # 组合索引
            if member_data["clean_name"] and member_data["clean_phone"]:
                combo_key = f"{member_data['clean_name']}:{member_data['clean_phone']}"
                if combo_key not in index["by_name_phone"]:
                    index["by_name_phone"][combo_key] = []
                index["by_name_phone"][combo_key].append(member_data)

            # 电话后缀索引优化（中国手机号后8位、7位、6位）
            if clean_phone and len(clean_phone) >= 6:
                for suffix_len in [8, 7, 6]:
                    if len(clean_phone) >= suffix_len:
                        suffix = clean_phone[-suffix_len:]
                        if suffix not in index["by_phone_suffix"]:
                            index["by_phone_suffix"][suffix] = []
                        index["by_phone_suffix"][suffix].append(member_data)

            # 姓名分组优化（按首字符分组以减少模糊匹配的搜索空间）
            if clean_name:
                first_char = clean_name[0] if clean_name else ""
                if first_char not in index["fuzzy_name_groups"]:
                    index["fuzzy_name_groups"][first_char] = []
                index["fuzzy_name_groups"][first_char].append(member_data)

        return index

    def _merge_b_table_data(
        self, member_index: Dict[str, Any], b_table_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """将B表数据合并到成员索引中"""
        for b_record in b_table_data:
            name = self._extract_name(b_record)
            phone = self._extract_phone(b_record)

            if not name and not phone:
                continue

            clean_name = self._clean_name(name)
            clean_phone = self._clean_phone(phone)

            # 尝试匹配现有成员
            matched = False

            # 优先通过组合键匹配
            if clean_name and clean_phone:
                combo_key = f"{clean_name}:{clean_phone}"
                if combo_key in member_index["by_name_phone"]:
                    for member_data in member_index["by_name_phone"][combo_key]:
                        member_data["b_data"] = b_record
                    matched = True

            # 通过姓名匹配
            if not matched and clean_name and clean_name in member_index["by_name"]:
                candidates = member_index["by_name"][clean_name]
                for member_data in candidates:
                    if self._phones_match(clean_phone, member_data["clean_phone"]):
                        member_data["b_data"] = b_record
                        matched = True
                        break

            # 通过电话匹配
            if not matched and clean_phone and clean_phone in member_index["by_phone"]:
                candidates = member_index["by_phone"][clean_phone]
                for member_data in candidates:
                    if self._names_similar(clean_name, member_data["clean_name"]):
                        member_data["b_data"] = b_record
                        matched = True
                        break

        return member_index

    async def _find_candidates_by_strategy(
        self,
        name: str,
        phone: str,
        email: str,
        member_index: Dict[str, Any],
        strategy: MatchingStrategy,
    ) -> List[Dict[str, Any]]:
        """根据策略查找候选匹配项"""
        candidates = []

        clean_name = self._clean_name(name)
        clean_phone = self._clean_phone(phone)

        if strategy == MatchingStrategy.EXACT:
            # 精确匹配
            combo_key = f"{clean_name}:{clean_phone}"
            if combo_key in member_index["by_name_phone"]:
                candidates.extend(member_index["by_name_phone"][combo_key])

        elif strategy == MatchingStrategy.FUZZY:
            # 模糊匹配
            candidates = self._fuzzy_search(clean_name, clean_phone, member_index)

        elif strategy == MatchingStrategy.MULTI_FIELD:
            # 多字段匹配
            candidates = self._multi_field_search(
                clean_name, clean_phone, email, member_index
            )

        return candidates

    def _fuzzy_search(
        self, clean_name: str, clean_phone: str, member_index: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """模糊搜索候选项（优化版）"""
        candidates = []
        seen_members = set()

        # 优化的姓名模糊匹配：只在相同首字符的组内搜索
        if clean_name:
            first_char = clean_name[0] if clean_name else ""
            search_groups = []

            # 主要搜索：相同首字符的组
            if first_char in member_index["fuzzy_name_groups"]:
                search_groups.extend(member_index["fuzzy_name_groups"][first_char])

            # 扩展搜索：相似发音的首字符（中文姓名优化）
            similar_chars = self._get_similar_first_chars(first_char)
            for similar_char in similar_chars:
                if similar_char in member_index["fuzzy_name_groups"]:
                    search_groups.extend(
                        member_index["fuzzy_name_groups"][similar_char]
                    )

            # 在筛选后的组内进行模糊匹配
            for member_data in search_groups:
                if self._names_similar(
                    clean_name, member_data["clean_name"], threshold=0.7
                ):
                    member_id = member_data["member"].id
                    if member_id not in seen_members:
                        candidates.append(member_data)
                        seen_members.add(member_id)

        # 优化的电话模糊匹配：使用后缀索引
        if clean_phone and len(clean_phone) >= 6:
            # 按后缀长度从长到短搜索，提高匹配精度
            for suffix_len in [8, 7, 6]:
                if len(clean_phone) >= suffix_len:
                    suffix = clean_phone[-suffix_len:]
                    if suffix in member_index["by_phone_suffix"]:
                        for member_data in member_index["by_phone_suffix"][suffix]:
                            member_id = member_data["member"].id
                            if member_id not in seen_members:
                                # 验证电话号码确实匹配
                                if self._phones_match(
                                    clean_phone, member_data["clean_phone"]
                                ):
                                    candidates.append(member_data)
                                    seen_members.add(member_id)
                        # 如果找到足够的候选项，停止搜索更短的后缀
                        if len(candidates) >= 10:  # 限制候选项数量
                            break

        return candidates

    def _get_similar_first_chars(self, char: str) -> List[str]:
        """获取相似发音的首字符（中文姓名优化）"""
        # 常见中文姓氏的相似发音映射
        similar_map = {
            "张": ["章", "长"],
            "王": ["汪"],
            "李": ["理", "里"],
            "刘": ["留", "柳"],
            "陈": ["程", "成"],
            "杨": ["羊", "洋"],
            "黄": ["王"],
            "吴": ["胡", "武"],
            "林": ["临"],
            "何": ["贺"],
        }
        return similar_map.get(char, [])

    def _multi_field_search(
        self,
        clean_name: str,
        clean_phone: str,
        email: str,
        member_index: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """多字段组合搜索"""
        candidates = []
        seen_members = set()

        # 收集所有可能的候选项
        all_candidates = []

        # 从姓名索引收集
        if clean_name:
            for indexed_name, member_list in member_index["by_name"].items():
                if self._names_similar(clean_name, indexed_name, threshold=0.5):
                    all_candidates.extend(member_list)

        # 从电话索引收集
        if clean_phone:
            for indexed_phone, member_list in member_index["by_phone"].items():
                if self._phones_match(clean_phone, indexed_phone, strict=False):
                    all_candidates.extend(member_list)

        # 从邮箱索引收集
        if email:
            email_lower = email.lower()
            if email_lower in member_index["by_email"]:
                all_candidates.extend(member_index["by_email"][email_lower])

        # 去重并返回
        for member_data in all_candidates:
            member_id = member_data["member"].id
            if member_id not in seen_members:
                candidates.append(member_data)
                seen_members.add(member_id)

        return candidates

    def _calculate_match_confidence(
        self,
        a_data: Dict[str, str],
        candidate: Dict[str, Any],
        strategy: MatchingStrategy,
    ) -> float:
        """计算匹配置信度"""
        try:
            total_score = 0.0
            total_weight = 0.0

            # 姓名匹配得分
            if a_data.get("name") and candidate.get("clean_name"):
                name_score = self._name_similarity_score(
                    self._clean_name(a_data["name"]), candidate["clean_name"]
                )
                total_score += name_score * self.field_weights["name"]
                total_weight += self.field_weights["name"]

            # 电话匹配得分
            if a_data.get("phone") and candidate.get("clean_phone"):
                phone_score = self._phone_similarity_score(
                    self._clean_phone(a_data["phone"]), candidate["clean_phone"]
                )
                total_score += phone_score * self.field_weights["phone"]
                total_weight += self.field_weights["phone"]

            # 邮箱匹配得分
            if a_data.get("email") and candidate.get("email"):
                email_score = (
                    1.0
                    if a_data["email"].lower() == candidate["email"].lower()
                    else 0.0
                )
                total_score += email_score * self.field_weights["email"]
                total_weight += self.field_weights["email"]

            # 策略加成
            if strategy == MatchingStrategy.EXACT:
                total_score *= 1.1  # 精确匹配有10%加成
            elif strategy == MatchingStrategy.MULTI_FIELD:
                total_score *= 1.05  # 多字段匹配有5%加成

            # 归一化到0-1范围
            confidence = min(
                total_score / total_weight if total_weight > 0 else 0.0, 1.0
            )

            return confidence

        except Exception as e:
            logger.warning(f"Confidence calculation error: {str(e)}")
            return 0.0

    def _clean_name(self, name: str) -> str:
        """清理姓名字符串"""
        if not name:
            return ""

        # 移除空格和特殊字符，保留中文、英文、·符号
        cleaned = self._name_clean_pattern.sub("", name.strip())
        return cleaned.lower()

    def _clean_phone(self, phone: str) -> str:
        """清理电话号码"""
        if not phone:
            return ""

        # 只保留数字和+号
        cleaned = self._phone_clean_pattern.sub("", str(phone))

        # 处理+86前缀
        if cleaned.startswith("+86"):
            cleaned = cleaned[3:]
        elif cleaned.startswith("86") and len(cleaned) == 13:
            cleaned = cleaned[2:]

        return cleaned

    def _names_similar(self, name1: str, name2: str, threshold: float = 0.8) -> bool:
        """判断两个姓名是否相似"""
        if not name1 or not name2:
            return False

        return self._name_similarity_score(name1, name2) >= threshold

    def _name_similarity_score(self, name1: str, name2: str) -> float:
        """计算姓名相似度得分（优化版）"""
        if not name1 or not name2:
            return 0.0

        # 使用缓存键优化
        cache_key = self._get_cache_key(name1, name2)
        if cache_key in self._name_cache:
            self._cache_hits += 1
            return self._name_cache[cache_key]

        self._cache_misses += 1

        # 完全匹配
        if name1 == name2:
            score = 1.0
        # 包含关系
        elif name1 in name2 or name2 in name1:
            score = 0.8
        # 长度差异过大的早期终止
        elif abs(len(name1) - len(name2)) > max(len(name1), len(name2)) * 0.7:
            score = 0.0
        else:
            # 使用优化的编辑距离算法
            score = self._optimized_levenshtein_similarity(name1, name2)

        # 缓存结果
        self._name_cache[cache_key] = score
        return score

    def _phones_match(self, phone1: str, phone2: str, strict: bool = True) -> bool:
        """判断两个电话号码是否匹配"""
        if not phone1 or not phone2:
            return False

        # 完全匹配
        if phone1 == phone2:
            return True

        # 后8位匹配（中国手机号）
        if len(phone1) >= 8 and len(phone2) >= 8:
            if phone1[-8:] == phone2[-8:]:
                return True

        # 非严格模式下，后7位匹配也可以
        if not strict and len(phone1) >= 7 and len(phone2) >= 7:
            if phone1[-7:] == phone2[-7:]:
                return True

        return False

    def _phone_similarity_score(self, phone1: str, phone2: str) -> float:
        """计算电话号码相似度得分（优化版）"""
        if not phone1 or not phone2:
            return 0.0

        # 使用缓存
        cache_key = self._get_cache_key(phone1, phone2)
        if cache_key in self._phone_cache:
            self._cache_hits += 1
            return self._phone_cache[cache_key]

        self._cache_misses += 1

        score = 0.0
        if phone1 == phone2:
            score = 1.0
        # 后8位匹配（中国手机号标准）
        elif len(phone1) >= 8 and len(phone2) >= 8 and phone1[-8:] == phone2[-8:]:
            score = 0.95
        # 后7位匹配
        elif len(phone1) >= 7 and len(phone2) >= 7 and phone1[-7:] == phone2[-7:]:
            score = 0.85
        # 后6位匹配（较宽松）
        elif len(phone1) >= 6 and len(phone2) >= 6 and phone1[-6:] == phone2[-6:]:
            score = 0.70

        # 缓存结果
        self._phone_cache[cache_key] = score
        return score

    def _levenshtein_similarity(self, s1: str, s2: str) -> float:
        """计算编辑距离相似度"""
        return self._optimized_levenshtein_similarity(s1, s2)

    def _optimized_levenshtein_similarity(self, s1: str, s2: str) -> float:
        """优化的编辑距离相似度计算"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0

        # 检查缓存
        cache_key = self._get_cache_key(s1, s2)
        if cache_key in self._similarity_cache:
            self._cache_hits += 1
            return self._similarity_cache[cache_key]

        self._cache_misses += 1

        m, n = len(s1), len(s2)

        # 早期终止优化：如果长度差异过大，直接返回低相似度
        max_len = max(m, n)
        min_len = min(m, n)
        if max_len > 0 and min_len / max_len < 0.3:  # 长度比例小于30%
            result = 0.0
            self._similarity_cache[cache_key] = result
            return result

        # 使用更高效的两行DP优化
        if m > n:
            s1, s2 = s2, s1
            m, n = n, m

        # 只使用两行的空间优化
        prev_row = list(range(n + 1))
        curr_row = [0] * (n + 1)

        for i in range(1, m + 1):
            curr_row[0] = i
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    curr_row[j] = prev_row[j - 1]
                else:
                    curr_row[j] = min(
                        prev_row[j] + 1,  # 删除
                        curr_row[j - 1] + 1,  # 插入
                        prev_row[j - 1] + 1,  # 替换
                    )
            prev_row, curr_row = curr_row, prev_row

        # 转换为相似度 (0-1)
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            result = 1.0
        else:
            result = 1.0 - prev_row[n] / max_len

        # 缓存结果
        self._similarity_cache[cache_key] = result
        return result

    def _get_cache_key(self, s1: str, s2: str) -> str:
        """生成缓存键"""
        # 确保键的顺序一致，避免重复缓存
        if s1 <= s2:
            return f"{s1}||{s2}"
        return f"{s2}||{s1}"

    def clear_cache(self) -> Dict[str, int]:
        """清理缓存并返回统计信息"""
        stats = {
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": self._cache_hits
            / max(self._cache_hits + self._cache_misses, 1),
            "cached_similarities": len(self._similarity_cache),
            "cached_names": len(self._name_cache),
            "cached_phones": len(self._phone_cache),
        }

        self._similarity_cache.clear()
        self._name_cache.clear()
        self._phone_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0

        return stats

    def _extract_name(self, record: Dict[str, Any]) -> str:
        """从记录中提取姓名"""
        name_fields = [
            "name",
            "姓名",
            "reporter_name",
            "报告人",
            "申请人",
            "联系人",
            "真实姓名",
        ]

        for field in name_fields:
            if field in record and record[field]:
                return str(record[field]).strip()

        return ""

    def _extract_phone(self, record: Dict[str, Any]) -> str:
        """从记录中提取电话号码"""
        phone_fields = [
            "phone",
            "contact",
            "联系方式",
            "联系电话",
            "手机号",
            "电话",
            "手机",
        ]

        for field in phone_fields:
            if field in record and record[field]:
                return str(record[field]).strip()

        return ""

    def _extract_email(self, record: Dict[str, Any]) -> str:
        """从记录中提取邮箱"""
        email_fields = ["email", "邮箱", "电子邮件", "邮件地址"]

        for field in email_fields:
            if field in record and record[field]:
                email = str(record[field]).strip()
                if "@" in email:
                    return email.lower()

        return ""

    def _get_confidence_level(self, confidence: float) -> MatchConfidence:
        """根据置信度数值获取等级"""
        if confidence >= self.thresholds["high_confidence"]:
            return MatchConfidence.HIGH
        elif confidence >= self.thresholds["medium_confidence"]:
            return MatchConfidence.MEDIUM
        elif confidence >= self.thresholds["low_confidence"]:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.VERY_LOW

    def _build_match_details(
        self, a_data: Dict[str, str], candidate: Dict[str, Any], confidence: float
    ) -> Dict[str, Any]:
        """构建匹配详情"""
        return {
            "confidence_score": confidence,
            "matched_fields": {
                "name": {
                    "a_value": a_data.get("name", ""),
                    "b_value": candidate.get("clean_name", ""),
                    "similarity": self._name_similarity_score(
                        self._clean_name(a_data.get("name", "")),
                        candidate.get("clean_name", ""),
                    ),
                },
                "phone": {
                    "a_value": a_data.get("phone", ""),
                    "b_value": candidate.get("clean_phone", ""),
                    "similarity": self._phone_similarity_score(
                        self._clean_phone(a_data.get("phone", "")),
                        candidate.get("clean_phone", ""),
                    ),
                },
            },
            "member_info": {
                "id": candidate["member"].id,
                "name": candidate["member"].name,
                "student_id": getattr(candidate["member"], "student_id", ""),
                "department": getattr(candidate["member"], "department", ""),
            },
            "has_b_data": candidate.get("b_data") is not None,
        }

    def _calculate_matching_stats(self, results: List[MatchResult]) -> Dict[str, Any]:
        """计算匹配统计信息"""
        total = len(results)
        if total == 0:
            return {"total": 0, "matched": 0, "match_rate": 0.0}

        matched = sum(1 for r in results if r.is_matched)
        high_confidence = sum(
            1 for r in results if r.confidence_level == MatchConfidence.HIGH
        )
        medium_confidence = sum(
            1 for r in results if r.confidence_level == MatchConfidence.MEDIUM
        )
        low_confidence = sum(
            1 for r in results if r.confidence_level == MatchConfidence.LOW
        )

        return {
            "total": total,
            "matched": matched,
            "match_rate": matched / total,
            "confidence_distribution": {
                "high": high_confidence,
                "medium": medium_confidence,
                "low": low_confidence,
                "very_low": total - matched,
            },
            "average_confidence": (
                sum(r.confidence for r in results) / total if total > 0 else 0.0
            ),
        }

    async def match_tables(
        self,
        a_table_data: List[Dict[str, Any]],
        b_table_data: Optional[List[Dict[str, Any]]] = None,
        strategies: Optional[List[MatchingStrategy]] = None,
        batch_size: int = 100,
        timeout_seconds: int = 240,
    ) -> List[MatchResult]:
        """
        匹配表格数据（别名方法，兼容现有调用）

        Args:
            a_table_data: A表数据
            b_table_data: B表数据（可选）
            strategies: 匹配策略列表
            batch_size: 批处理大小
            timeout_seconds: 超时时间（秒）

        Returns:
            List[MatchResult]: 匹配结果列表
        """
        # 直接调用主匹配方法
        return await self.match_ab_tables(
            a_table_data=a_table_data,
            b_table_data=b_table_data,
            strategies=strategies,
            batch_size=batch_size,
            timeout_seconds=timeout_seconds,
        )
