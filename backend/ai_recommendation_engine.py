#!/usr/bin/env python3
"""
AI增强的建议生成系统
结合传统规则和大模型API的混合推荐引擎
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import openai
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RecommendationContext:
    """建议生成上下文"""
    test_results: Dict[str, Any]
    code_changes: List[str]
    historical_patterns: Dict[str, Any]
    team_profile: Dict[str, Any]
    system_metrics: Dict[str, Any]


@dataclass
class Recommendation:
    """单个建议结构"""
    title: str
    description: str
    priority: str  # "high", "medium", "low"
    category: str  # "performance", "quality", "reliability", "security"
    implementation_steps: List[str]
    expected_impact: str
    effort_estimate: str
    confidence_score: float


class LLMRecommendationService:
    """大模型建议生成服务"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.system_context = self._build_system_context()
    
    def _build_system_context(self) -> str:
        """构建系统上下文提示"""
        return """
你是一个专业的软件质量分析专家，专门为考勤管理系统提供技术改进建议。

你的专业领域包括：
- Python/FastAPI后端开发
- PostgreSQL数据库优化
- SQLAlchemy ORM性能调优
- 测试自动化和CI/CD
- 系统架构和性能优化

分析风格要求：
1. 深入分析根本原因，不只是表面现象
2. 提供具体可执行的改进步骤
3. 评估每个建议的优先级和预期影响
4. 考虑实施成本和技术风险
5. 结合业务场景提供实用建议

输出格式：
- 使用结构化的JSON格式
- 包含优先级、分类、实施步骤等详细信息
- 提供置信度评分
"""
    
    async def generate_recommendations(
        self, 
        context: RecommendationContext
    ) -> List[Recommendation]:
        """生成AI驱动的建议"""
        try:
            prompt = self._build_analysis_prompt(context)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_context},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 保持一致性
                max_tokens=3000
            )
            
            return self._parse_ai_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI建议生成失败: {e}")
            return []
    
    def _build_analysis_prompt(self, context: RecommendationContext) -> str:
        """构建分析提示"""
        prompt = f"""
请分析以下考勤系统的测试数据和上下文信息，提供专业的改进建议：

## 测试结果数据
```json
{json.dumps(context.test_results, indent=2, ensure_ascii=False)}
```

## 最近代码变更
{chr(10).join(context.code_changes)}

## 历史问题模式
```json
{json.dumps(context.historical_patterns, indent=2, ensure_ascii=False)}
```

## 团队技术概况
```json
{json.dumps(context.team_profile, indent=2, ensure_ascii=False)}
```

## 系统性能指标
```json
{json.dumps(context.system_metrics, indent=2, ensure_ascii=False)}
```

## 分析要求

请从以下维度进行深度分析：

1. **根本原因分析**: 识别测试失败和性能问题的深层次原因
2. **影响评估**: 评估问题对系统稳定性和用户体验的影响
3. **解决方案**: 提供具体、可执行的技术解决方案
4. **优先级排序**: 基于影响程度和实施难度进行优先级排序
5. **实施路径**: 详细的实施步骤和时间规划

## 输出格式

请返回JSON格式的建议列表：

```json
{{
  "recommendations": [
    {{
      "title": "建议标题",
      "description": "详细描述问题和解决方案",
      "priority": "high|medium|low",
      "category": "performance|quality|reliability|security",
      "implementation_steps": [
        "具体实施步骤1",
        "具体实施步骤2"
      ],
      "expected_impact": "预期影响描述",
      "effort_estimate": "预估工作量",
      "confidence_score": 0.85
    }}
  ],
  "analysis_summary": "整体分析总结",
  "risk_assessment": "风险评估和注意事项"
}}
```

现在开始分析并提供建议：
"""
        return prompt
    
    def _parse_ai_response(self, response_text: str) -> List[Recommendation]:
        """解析AI响应为结构化建议"""
        try:
            # 尝试解析JSON响应
            data = json.loads(response_text)
            recommendations = []
            
            for rec_data in data.get("recommendations", []):
                recommendation = Recommendation(
                    title=rec_data.get("title", ""),
                    description=rec_data.get("description", ""),
                    priority=rec_data.get("priority", "medium"),
                    category=rec_data.get("category", "quality"),
                    implementation_steps=rec_data.get("implementation_steps", []),
                    expected_impact=rec_data.get("expected_impact", ""),
                    effort_estimate=rec_data.get("effort_estimate", ""),
                    confidence_score=rec_data.get("confidence_score", 0.7)
                )
                recommendations.append(recommendation)
            
            return recommendations
            
        except json.JSONDecodeError:
            logger.error("无法解析AI响应为JSON格式")
            return []


class TraditionalRuleEngine:
    """传统规则引擎"""
    
    def generate_recommendations(
        self, 
        test_results: Dict[str, Any]
    ) -> List[Recommendation]:
        """基于规则生成建议"""
        recommendations = []
        stats = test_results.get("statistics", {})
        
        # 测试失败建议
        if stats.get("failed", 0) > 0:
            recommendations.append(Recommendation(
                title="修复失败的测试用例",
                description=f"发现 {stats['failed']} 个失败的测试用例，需要优先修复",
                priority="high",
                category="reliability",
                implementation_steps=[
                    "分析失败测试的错误日志",
                    "定位问题根源",
                    "修复相关代码",
                    "验证修复效果"
                ],
                expected_impact="提升系统稳定性",
                effort_estimate="2-4小时",
                confidence_score=0.9
            ))
        
        # 性能建议
        metrics = test_results.get("performance_metrics", {})
        avg_response_time = metrics.get("average_response_time", 0)
        
        if avg_response_time > 500:
            recommendations.append(Recommendation(
                title="优化API响应性能",
                description=f"平均响应时间{avg_response_time}ms，超过推荐阈值",
                priority="medium",
                category="performance",
                implementation_steps=[
                    "分析慢查询日志",
                    "添加数据库索引",
                    "实施缓存策略",
                    "优化数据库查询"
                ],
                expected_impact="响应时间减少50%",
                effort_estimate="1-2天",
                confidence_score=0.8
            ))
        
        return recommendations


class HybridRecommendationEngine:
    """混合推荐引擎：结合规则和AI"""
    
    def __init__(self, llm_service: Optional[LLMRecommendationService] = None):
        self.rule_engine = TraditionalRuleEngine()
        self.llm_service = llm_service
        self.enable_ai = llm_service is not None
    
    async def generate_recommendations(
        self, 
        context: RecommendationContext
    ) -> Dict[str, Any]:
        """生成混合建议"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "ai_enabled": self.enable_ai,
            "recommendations": [],
            "metadata": {}
        }
        
        # 1. 生成传统规则建议
        rule_recommendations = self.rule_engine.generate_recommendations(
            context.test_results
        )
        
        # 2. 如果启用AI，生成AI建议
        ai_recommendations = []
        if self.enable_ai:
            try:
                ai_recommendations = await self.llm_service.generate_recommendations(context)
                result["metadata"]["ai_analysis_success"] = True
            except Exception as e:
                logger.error(f"AI分析失败，降级到规则引擎: {e}")
                result["metadata"]["ai_analysis_success"] = False
        
        # 3. 智能融合建议
        merged_recommendations = self._merge_recommendations(
            rule_recommendations, 
            ai_recommendations
        )
        
        result["recommendations"] = [rec.__dict__ for rec in merged_recommendations]
        result["metadata"]["total_recommendations"] = len(merged_recommendations)
        result["metadata"]["rule_recommendations"] = len(rule_recommendations)
        result["metadata"]["ai_recommendations"] = len(ai_recommendations)
        
        return result
    
    def _merge_recommendations(
        self, 
        rule_recs: List[Recommendation], 
        ai_recs: List[Recommendation]
    ) -> List[Recommendation]:
        """智能合并两种建议"""
        merged = []
        
        # 去重和优先级调整逻辑
        seen_titles = set()
        
        # 优先处理高优先级的AI建议
        for rec in sorted(ai_recs, key=lambda x: self._priority_score(x.priority), reverse=True):
            if rec.title not in seen_titles:
                merged.append(rec)
                seen_titles.add(rec.title)
        
        # 添加不重复的规则建议
        for rec in rule_recs:
            if rec.title not in seen_titles:
                merged.append(rec)
                seen_titles.add(rec.title)
        
        # 按优先级和置信度排序
        return sorted(merged, key=lambda x: (
            self._priority_score(x.priority),
            x.confidence_score
        ), reverse=True)
    
    def _priority_score(self, priority: str) -> int:
        """优先级评分"""
        return {"high": 3, "medium": 2, "low": 1}.get(priority, 1)


class EnhancedRecommendationSystem:
    """增强的建议生成系统"""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.llm_service = None
        if openai_api_key:
            self.llm_service = LLMRecommendationService(openai_api_key)
        
        self.hybrid_engine = HybridRecommendationEngine(self.llm_service)
    
    async def analyze_and_recommend(
        self, 
        test_results: Dict[str, Any],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分析并生成建议"""
        
        # 构建分析上下文
        context = RecommendationContext(
            test_results=test_results,
            code_changes=self._get_recent_changes(),
            historical_patterns=self._get_historical_patterns(),
            team_profile=self._get_team_profile(),
            system_metrics=self._get_system_metrics()
        )
        
        # 生成建议
        recommendations = await self.hybrid_engine.generate_recommendations(context)
        
        # 保存结果
        await self._save_recommendations(recommendations)
        
        return recommendations
    
    def _get_recent_changes(self) -> List[str]:
        """获取最近的代码变更"""
        # 这里可以集成git信息
        return [
            "修改了用户认证逻辑",
            "更新了数据库迁移脚本", 
            "优化了API响应格式"
        ]
    
    def _get_historical_patterns(self) -> Dict[str, Any]:
        """获取历史问题模式"""
        return {
            "common_failures": ["database_connection", "enum_creation"],
            "performance_trends": {"response_time_trend": "improving"},
            "fix_success_rate": 0.85
        }
    
    def _get_team_profile(self) -> Dict[str, Any]:
        """获取团队技术概况"""
        return {
            "tech_stack": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy"],
            "experience_level": "intermediate",
            "team_size": 3,
            "project_phase": "development"
        }
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        return {
            "uptime": 0.99,
            "error_rate": 0.02,
            "avg_response_time": 450,
            "database_performance": "good"
        }
    
    async def _save_recommendations(self, recommendations: Dict[str, Any]):
        """保存建议到文件"""
        output_dir = Path("reports/ai_recommendations")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ai_recommendations_{timestamp}.json"
        
        with open(output_dir / filename, "w", encoding="utf-8") as f:
            json.dump(recommendations, f, indent=2, ensure_ascii=False)
        
        logger.info(f"AI建议已保存到: {output_dir / filename}")


# 使用示例
async def main():
    """主函数演示"""
    # 模拟测试结果
    test_results = {
        "statistics": {
            "total_tests": 25,
            "passed": 22,
            "failed": 2,
            "skipped": 1,
            "errors": 0
        },
        "performance_metrics": {
            "average_response_time": 650,
            "slowest_endpoint": 1200
        },
        "failures": [
            {
                "test_name": "test_database_connection",
                "error_message": "UserRole enum creation failed"
            }
        ]
    }
    
    # 创建AI增强建议系统（需要OpenAI API密钥）
    # system = EnhancedRecommendationSystem("your-openai-api-key")
    
    # 创建传统建议系统（无需API密钥）
    system = EnhancedRecommendationSystem()
    
    # 生成建议
    recommendations = await system.analyze_and_recommend(test_results)
    
    # 输出结果
    print("=== AI增强建议系统分析结果 ===")
    print(f"生成时间: {recommendations['timestamp']}")
    print(f"AI分析: {'启用' if recommendations['ai_enabled'] else '未启用'}")
    print(f"建议总数: {recommendations['metadata']['total_recommendations']}")
    print()
    
    for i, rec in enumerate(recommendations['recommendations'], 1):
        print(f"{i}. 【{rec['priority'].upper()}】{rec['title']}")
        print(f"   分类: {rec['category']}")
        print(f"   描述: {rec['description']}")
        print(f"   预期影响: {rec['expected_impact']}")
        print(f"   工作量估算: {rec['effort_estimate']}")
        print(f"   置信度: {rec['confidence_score']:.2f}")
        print()


if __name__ == "__main__":
    asyncio.run(main())
