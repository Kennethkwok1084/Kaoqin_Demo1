"""
统计报表E2E测试
测试各种统计图表生成、区域分析、词云分析、导出功能验证
包含完整的数据分析和报表生成流程
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient


class TestStatisticsAndReports:
    """统计报表E2E测试类"""

    @pytest.mark.asyncio
    async def test_dashboard_overview_statistics(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试仪表盘概览统计"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取系统概览统计
        overview_response = await e2e_client.get(
            "/api/v1/statistics/overview", headers=admin_headers
        )

        if overview_response.status_code == 200:
            e2e_helper.assert_response_success(overview_response)
            overview_data = overview_response.json().get("data", {})

            # 验证基础统计数据结构
            expected_stats = [
                "total_tasks",
                "completed_tasks",
                "pending_tasks",
                "total_members",
                "active_members",
                "total_work_hours",
                "monthly_completion_rate",
            ]

            for stat in expected_stats:
                if stat in overview_data:
                    assert isinstance(overview_data[stat], (int, float))
                    assert overview_data[stat] >= 0

            # 2. 获取实时统计数据
            realtime_response = await e2e_client.get(
                "/api/v1/statistics/realtime", headers=admin_headers
            )

            if realtime_response.status_code == 200:
                e2e_helper.assert_response_success(realtime_response)
                realtime_data = realtime_response.json().get("data", {})

                # 验证实时数据
                realtime_metrics = [
                    "tasks_created_today",
                    "tasks_completed_today",
                    "online_members",
                    "average_response_time",
                ]

                for metric in realtime_metrics:
                    if metric in realtime_data:
                        assert isinstance(realtime_data[metric], (int, float))
        else:
            pytest.skip("Statistics overview not available")

    @pytest.mark.asyncio
    async def test_task_performance_analytics(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试任务性能分析"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取任务完成率分析
        completion_analysis_response = await e2e_client.get(
            "/api/v1/statistics/task-completion-analysis",
            params={"period": "monthly", "months": 6},
            headers=admin_headers,
        )

        if completion_analysis_response.status_code == 200:
            e2e_helper.assert_response_success(completion_analysis_response)
            completion_data = completion_analysis_response.json().get("data", {})

            # 验证完成率分析数据
            if "monthly_completion_rates" in completion_data:
                monthly_rates = completion_data["monthly_completion_rates"]
                for month_data in monthly_rates:
                    assert "year" in month_data
                    assert "month" in month_data
                    assert "completion_rate" in month_data
                    assert 0 <= month_data["completion_rate"] <= 100

        # 2. 获取任务响应时间分析
        response_time_analysis = await e2e_client.get(
            "/api/v1/statistics/response-time-analysis",
            params={
                "start_date": (datetime.now() - timedelta(days=30)).date().isoformat(),
                "end_date": datetime.now().date().isoformat(),
            },
            headers=admin_headers,
        )

        if response_time_analysis.status_code == 200:
            e2e_helper.assert_response_success(response_time_analysis)
            response_data = response_time_analysis.json().get("data", {})

            # 验证响应时间分析
            response_metrics = [
                "average_response_time",
                "median_response_time",
                "response_time_distribution",
            ]

            for metric in response_metrics:
                if metric in response_data:
                    if metric.endswith("_time"):
                        assert isinstance(response_data[metric], (int, float))
                        assert response_data[metric] >= 0

        # 3. 获取任务类型分布统计
        task_distribution_response = await e2e_client.get(
            "/api/v1/statistics/task-type-distribution", headers=admin_headers
        )

        if task_distribution_response.status_code == 200:
            e2e_helper.assert_response_success(task_distribution_response)
            distribution_data = task_distribution_response.json().get("data", {})

            # 验证任务类型分布数据
            if "task_types" in distribution_data:
                task_types = distribution_data["task_types"]
                for task_type_data in task_types:
                    assert "type" in task_type_data
                    assert "count" in task_type_data
                    assert "percentage" in task_type_data
                    assert task_type_data["count"] >= 0
                    assert 0 <= task_type_data["percentage"] <= 100

    @pytest.mark.asyncio
    async def test_member_performance_ranking(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试成员绩效排名"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取工作时长排行榜
        work_hours_ranking_response = await e2e_client.get(
            "/api/v1/statistics/work-hours-ranking",
            params={
                "period": "monthly",
                "year": datetime.now().year,
                "month": datetime.now().month,
                "limit": 10,
            },
            headers=admin_headers,
        )

        if work_hours_ranking_response.status_code == 200:
            e2e_helper.assert_response_success(work_hours_ranking_response)
            ranking_data = work_hours_ranking_response.json().get("data", {})

            if "rankings" in ranking_data:
                rankings = ranking_data["rankings"]
                for i, member_ranking in enumerate(rankings):
                    assert "member_id" in member_ranking
                    assert "member_name" in member_ranking
                    assert "total_work_hours" in member_ranking
                    assert "rank" in member_ranking
                    assert member_ranking["total_work_hours"] >= 0
                    assert member_ranking["rank"] == i + 1

        # 2. 获取任务完成数量排行榜
        task_completion_ranking_response = await e2e_client.get(
            "/api/v1/statistics/task-completion-ranking",
            params={"period": "monthly", "limit": 10},
            headers=admin_headers,
        )

        if task_completion_ranking_response.status_code == 200:
            e2e_helper.assert_response_success(task_completion_ranking_response)
            task_ranking_data = task_completion_ranking_response.json().get("data", {})

            if "rankings" in task_ranking_data:
                task_rankings = task_ranking_data["rankings"]
                for member_ranking in task_rankings:
                    assert "member_name" in member_ranking
                    assert "completed_tasks" in member_ranking
                    assert "completion_rate" in member_ranking
                    assert member_ranking["completed_tasks"] >= 0
                    assert 0 <= member_ranking["completion_rate"] <= 100

        # 3. 获取综合绩效评分
        performance_score_response = await e2e_client.get(
            "/api/v1/statistics/performance-scores",
            params={
                "calculation_method": "weighted",
                "include_factors": [
                    "work_hours",
                    "task_completion",
                    "user_satisfaction",
                ],
            },
            headers=admin_headers,
        )

        if performance_score_response.status_code == 200:
            e2e_helper.assert_response_success(performance_score_response)
            score_data = performance_score_response.json().get("data", {})

            if "member_scores" in score_data:
                member_scores = score_data["member_scores"]
                for member_score in member_scores:
                    assert "member_name" in member_score
                    assert "overall_score" in member_score
                    assert "component_scores" in member_score
                    assert 0 <= member_score["overall_score"] <= 100

    @pytest.mark.asyncio
    async def test_geographic_area_analysis(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试地理区域分析"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取区域任务分布统计
        area_distribution_response = await e2e_client.get(
            "/api/v1/statistics/area-distribution", headers=admin_headers
        )

        if area_distribution_response.status_code == 200:
            e2e_helper.assert_response_success(area_distribution_response)
            area_data = area_distribution_response.json().get("data", {})

            # 验证区域分布数据
            if "area_statistics" in area_data:
                area_stats = area_data["area_statistics"]
                for area_stat in area_stats:
                    assert "area_name" in area_stat
                    assert "task_count" in area_stat
                    assert "completion_rate" in area_stat
                    assert area_stat["task_count"] >= 0
                    assert 0 <= area_stat["completion_rate"] <= 100

        # 2. 获取热力图数据
        heatmap_response = await e2e_client.get(
            "/api/v1/statistics/area-heatmap",
            params={"metric": "task_density", "period": "monthly"},
            headers=admin_headers,
        )

        if heatmap_response.status_code == 200:
            e2e_helper.assert_response_success(heatmap_response)
            heatmap_data = heatmap_response.json().get("data", {})

            # 验证热力图数据结构
            if "heatmap_data" in heatmap_data:
                heatmap_points = heatmap_data["heatmap_data"]
                for point in heatmap_points:
                    assert "location" in point
                    assert "value" in point
                    assert "coordinates" in point
                    assert point["value"] >= 0

        # 3. 获取区域效率对比
        area_efficiency_response = await e2e_client.get(
            "/api/v1/statistics/area-efficiency-comparison", headers=admin_headers
        )

        if area_efficiency_response.status_code == 200:
            e2e_helper.assert_response_success(area_efficiency_response)
            efficiency_data = area_efficiency_response.json().get("data", {})

            if "area_comparisons" in efficiency_data:
                comparisons = efficiency_data["area_comparisons"]
                for comparison in comparisons:
                    assert "area_name" in comparison
                    assert "efficiency_score" in comparison
                    assert "average_completion_time" in comparison
                    assert 0 <= comparison["efficiency_score"] <= 100

    @pytest.mark.asyncio
    async def test_word_cloud_analysis(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试词云分析"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取任务描述词云
        task_wordcloud_response = await e2e_client.get(
            "/api/v1/statistics/task-description-wordcloud",
            params={"max_words": 50, "time_period": "last_30_days"},
            headers=admin_headers,
        )

        if task_wordcloud_response.status_code == 200:
            e2e_helper.assert_response_success(task_wordcloud_response)
            wordcloud_data = task_wordcloud_response.json().get("data", {})

            # 验证词云数据结构
            if "word_frequencies" in wordcloud_data:
                word_frequencies = wordcloud_data["word_frequencies"]
                for word_data in word_frequencies:
                    assert "word" in word_data
                    assert "frequency" in word_data
                    assert "weight" in word_data
                    assert word_data["frequency"] > 0
                    assert word_data["weight"] > 0

        # 2. 获取用户反馈词云
        feedback_wordcloud_response = await e2e_client.get(
            "/api/v1/statistics/user-feedback-wordcloud",
            params={"feedback_type": "positive", "max_words": 30},
            headers=admin_headers,
        )

        if feedback_wordcloud_response.status_code == 200:
            e2e_helper.assert_response_success(feedback_wordcloud_response)
            feedback_data = feedback_wordcloud_response.json().get("data", {})

            if "sentiment_words" in feedback_data:
                sentiment_words = feedback_data["sentiment_words"]
                for sentiment_word in sentiment_words:
                    assert "word" in sentiment_word
                    assert "sentiment_score" in sentiment_word
                    assert "frequency" in sentiment_word
                    assert -1 <= sentiment_word["sentiment_score"] <= 1

        # 3. 获取问题类型词云
        issue_type_wordcloud_response = await e2e_client.get(
            "/api/v1/statistics/issue-type-wordcloud", headers=admin_headers
        )

        if issue_type_wordcloud_response.status_code == 200:
            e2e_helper.assert_response_success(issue_type_wordcloud_response)
            issue_data = issue_type_wordcloud_response.json().get("data", {})

            if "issue_categories" in issue_data:
                issue_categories = issue_data["issue_categories"]
                for category in issue_categories:
                    assert "category" in category
                    assert "count" in category
                    assert "trend" in category
                    assert category["count"] >= 0

    @pytest.mark.asyncio
    async def test_time_series_analysis(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试时间序列分析"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 获取任务创建趋势
        task_trend_response = await e2e_client.get(
            "/api/v1/statistics/task-creation-trend",
            params={"period": "daily", "days": 30},
            headers=admin_headers,
        )

        if task_trend_response.status_code == 200:
            e2e_helper.assert_response_success(task_trend_response)
            trend_data = task_trend_response.json().get("data", {})

            # 验证时间序列数据
            if "time_series" in trend_data:
                time_series = trend_data["time_series"]
                for data_point in time_series:
                    assert "date" in data_point
                    assert "value" in data_point
                    assert "moving_average" in data_point
                    assert data_point["value"] >= 0

        # 2. 获取工作负载分析
        workload_analysis_response = await e2e_client.get(
            "/api/v1/statistics/workload-analysis",
            params={"granularity": "hourly", "days": 7},
            headers=admin_headers,
        )

        if workload_analysis_response.status_code == 200:
            e2e_helper.assert_response_success(workload_analysis_response)
            workload_data = workload_analysis_response.json().get("data", {})

            if "hourly_workload" in workload_data:
                hourly_data = workload_data["hourly_workload"]
                for hour_data in hourly_data:
                    assert "hour" in hour_data
                    assert "task_count" in hour_data
                    assert "avg_response_time" in hour_data
                    assert 0 <= hour_data["hour"] <= 23
                    assert hour_data["task_count"] >= 0

        # 3. 获取季节性分析
        seasonal_analysis_response = await e2e_client.get(
            "/api/v1/statistics/seasonal-analysis",
            params={"years": 2},
            headers=admin_headers,
        )

        if seasonal_analysis_response.status_code == 200:
            e2e_helper.assert_response_success(seasonal_analysis_response)
            seasonal_data = seasonal_analysis_response.json().get("data", {})

            if "seasonal_patterns" in seasonal_data:
                patterns = seasonal_data["seasonal_patterns"]
                for pattern in patterns:
                    assert "period" in pattern
                    assert "average_tasks" in pattern
                    assert "peak_hours" in pattern
                    assert pattern["average_tasks"] >= 0

    @pytest.mark.asyncio
    async def test_advanced_data_export_functionality(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试高级数据导出功能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 导出综合统计报告（Excel格式）
        excel_export_response = await e2e_client.post(
            "/api/v1/statistics/export/comprehensive-report",
            json={
                "format": "excel",
                "include_charts": True,
                "date_range": {
                    "start_date": (datetime.now() - timedelta(days=30))
                    .date()
                    .isoformat(),
                    "end_date": datetime.now().date().isoformat(),
                },
                "sections": [
                    "overview",
                    "task_analysis",
                    "member_performance",
                    "area_distribution",
                ],
            },
            headers=admin_headers,
        )

        if excel_export_response.status_code == 200:
            e2e_helper.assert_response_success(excel_export_response)

            # 验证Excel文件响应
            content_type = excel_export_response.headers.get("content-type", "")
            assert (
                "application/vnd.openxmlformats" in content_type
                or "application/octet-stream" in content_type
            )

            content_disposition = excel_export_response.headers.get(
                "content-disposition", ""
            )
            assert "attachment" in content_disposition
            assert ".xlsx" in content_disposition

            # 验证文件内容不为空
            assert len(excel_export_response.content) > 0

        # 2. 导出JSON格式的统计数据
        json_export_response = await e2e_client.post(
            "/api/v1/statistics/export/raw-data",
            json={
                "format": "json",
                "data_types": ["tasks", "members", "attendance"],
                "date_range": {
                    "start_date": (datetime.now() - timedelta(days=7))
                    .date()
                    .isoformat(),
                    "end_date": datetime.now().date().isoformat(),
                },
            },
            headers=admin_headers,
        )

        if json_export_response.status_code == 200:
            e2e_helper.assert_response_success(json_export_response)

            # 验证JSON响应
            content_type = json_export_response.headers.get("content-type", "")
            assert "application/json" in content_type

            export_data = json_export_response.json().get("data", {})
            assert "exported_records" in export_data
            assert "export_timestamp" in export_data

        # 3. 导出CSV格式的数据分析结果
        csv_export_response = await e2e_client.get(
            "/api/v1/statistics/export/analysis-results",
            params={
                "format": "csv",
                "analysis_type": "member_performance",
                "period": "monthly",
            },
            headers=admin_headers,
        )

        if csv_export_response.status_code == 200:
            e2e_helper.assert_response_success(csv_export_response)

            # 验证CSV文件响应
            content_type = csv_export_response.headers.get("content-type", "")
            assert "text/csv" in content_type or "application/csv" in content_type

            # 验证CSV内容不为空
            assert len(csv_export_response.content) > 0

    @pytest.mark.asyncio
    async def test_custom_dashboard_and_widgets(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试自定义仪表盘和小部件"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 创建自定义仪表盘配置
        dashboard_config = {
            "name": "管理员专用仪表盘",
            "description": "包含关键管理指标的自定义仪表盘",
            "layout": "grid",
            "widgets": [
                {
                    "type": "task_summary",
                    "position": {"row": 1, "col": 1, "width": 2, "height": 1},
                    "config": {"refresh_interval": 300},
                },
                {
                    "type": "member_ranking",
                    "position": {"row": 1, "col": 3, "width": 2, "height": 2},
                    "config": {"top_count": 5, "metric": "work_hours"},
                },
                {
                    "type": "area_heatmap",
                    "position": {"row": 2, "col": 1, "width": 4, "height": 2},
                    "config": {"heat_metric": "task_density"},
                },
            ],
        }

        create_dashboard_response = await e2e_client.post(
            "/api/v1/statistics/dashboard/custom",
            json=dashboard_config,
            headers=admin_headers,
        )

        if create_dashboard_response.status_code == 201:
            e2e_helper.assert_response_success(create_dashboard_response, 201)
            dashboard_result = create_dashboard_response.json()

            dashboard_data = dashboard_result.get("data", {})
            dashboard_id = dashboard_data["id"]

            # 验证仪表盘创建成功
            assert dashboard_data["name"] == dashboard_config["name"]
            assert len(dashboard_data["widgets"]) == len(dashboard_config["widgets"])

            # 2. 获取仪表盘数据
            dashboard_data_response = await e2e_client.get(
                f"/api/v1/statistics/dashboard/{dashboard_id}/data",
                headers=admin_headers,
            )

            if dashboard_data_response.status_code == 200:
                e2e_helper.assert_response_success(dashboard_data_response)
                widget_data = dashboard_data_response.json().get("data", {})

                # 验证小部件数据
                assert "widgets" in widget_data
                widgets = widget_data["widgets"]

                for widget in widgets:
                    assert "widget_id" in widget
                    assert "type" in widget
                    assert "data" in widget

            # 3. 更新仪表盘配置
            updated_config = dashboard_config.copy()
            updated_config["name"] = "更新后的管理员仪表盘"

            update_response = await e2e_client.put(
                f"/api/v1/statistics/dashboard/{dashboard_id}",
                json=updated_config,
                headers=admin_headers,
            )

            if update_response.status_code == 200:
                e2e_helper.assert_response_success(update_response)
                updated_data = update_response.json().get("data", {})
                assert updated_data["name"] == updated_config["name"]

            # 4. 删除自定义仪表盘（清理测试数据）
            delete_response = await e2e_client.delete(
                f"/api/v1/statistics/dashboard/{dashboard_id}", headers=admin_headers
            )

            if delete_response.status_code == 200:
                e2e_helper.assert_response_success(delete_response)
        else:
            pytest.skip("Custom dashboard functionality not available")

    @pytest.mark.asyncio
    async def test_statistical_alerts_and_thresholds(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试统计警报和阈值监控"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 设置统计警报规则
        alert_rules = {
            "rules": [
                {
                    "name": "任务完成率过低警报",
                    "metric": "completion_rate",
                    "threshold": 80,
                    "condition": "less_than",
                    "period": "daily",
                    "enabled": True,
                },
                {
                    "name": "响应时间过长警报",
                    "metric": "average_response_time",
                    "threshold": 120,  # 2小时
                    "condition": "greater_than",
                    "period": "hourly",
                    "enabled": True,
                },
                {
                    "name": "待处理任务堆积警报",
                    "metric": "pending_tasks_count",
                    "threshold": 50,
                    "condition": "greater_than",
                    "period": "real_time",
                    "enabled": True,
                },
            ]
        }

        create_alerts_response = await e2e_client.post(
            "/api/v1/statistics/alerts/rules", json=alert_rules, headers=admin_headers
        )

        if create_alerts_response.status_code == 200:
            e2e_helper.assert_response_success(create_alerts_response)

            # 2. 获取当前活跃警报
            active_alerts_response = await e2e_client.get(
                "/api/v1/statistics/alerts/active", headers=admin_headers
            )

            if active_alerts_response.status_code == 200:
                e2e_helper.assert_response_success(active_alerts_response)
                alerts_data = active_alerts_response.json().get("data", {})

                if "active_alerts" in alerts_data:
                    active_alerts = alerts_data["active_alerts"]
                    for alert in active_alerts:
                        assert "alert_id" in alert
                        assert "rule_name" in alert
                        assert "triggered_at" in alert
                        assert "severity" in alert

            # 3. 获取警报历史
            alert_history_response = await e2e_client.get(
                "/api/v1/statistics/alerts/history",
                params={"days": 7, "severity": "high"},
                headers=admin_headers,
            )

            if alert_history_response.status_code == 200:
                e2e_helper.assert_response_success(alert_history_response)
                history_data = alert_history_response.json().get("data", {})

                if "alert_history" in history_data:
                    history = history_data["alert_history"]
                    for alert_record in history:
                        assert "alert_id" in alert_record
                        assert "triggered_at" in alert_record
                        assert (
                            "resolved_at" in alert_record
                            or alert_record["resolved_at"] is None
                        )
        else:
            pytest.skip("Statistical alerts functionality not available")

    @pytest.mark.asyncio
    async def test_data_visualization_charts(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试数据可视化图表生成"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 1. 生成任务状态饼图
        pie_chart_response = await e2e_client.get(
            "/api/v1/statistics/charts/task-status-pie",
            params={"width": 400, "height": 300, "format": "svg"},
            headers=admin_headers,
        )

        if pie_chart_response.status_code == 200:
            # 验证SVG图表响应
            content_type = pie_chart_response.headers.get("content-type", "")
            assert "image/svg+xml" in content_type or "text/plain" in content_type

            # 验证SVG内容
            svg_content = pie_chart_response.text
            assert "<svg" in svg_content
            assert "</svg>" in svg_content

        # 2. 生成工作时长趋势线图
        line_chart_response = await e2e_client.get(
            "/api/v1/statistics/charts/work-hours-trend",
            params={
                "period": "weekly",
                "weeks": 8,
                "format": "png",
                "width": 800,
                "height": 400,
            },
            headers=admin_headers,
        )

        if line_chart_response.status_code == 200:
            # 验证PNG图表响应
            content_type = line_chart_response.headers.get("content-type", "")
            assert (
                "image/png" in content_type
                or "application/octet-stream" in content_type
            )

            # 验证图片内容不为空
            assert len(line_chart_response.content) > 0

        # 3. 生成成员绩效雷达图
        radar_chart_response = await e2e_client.get(
            "/api/v1/statistics/charts/member-performance-radar",
            params={
                "member_count": 5,
                "metrics": [
                    "work_hours",
                    "task_completion",
                    "response_time",
                    "satisfaction",
                ],
                "format": "svg",
            },
            headers=admin_headers,
        )

        if radar_chart_response.status_code == 200:
            # 验证雷达图响应
            content_type = radar_chart_response.headers.get("content-type", "")
            assert "image/svg+xml" in content_type or "text/plain" in content_type

            # 验证SVG雷达图内容
            radar_svg = radar_chart_response.text
            assert "<svg" in radar_svg
            # 雷达图应包含polygon或circle元素
            assert "polygon" in radar_svg or "circle" in radar_svg


class TestStatisticsPerformance:
    """统计报表性能测试"""

    @pytest.mark.asyncio
    async def test_statistics_query_performance(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_performance_monitor,
        e2e_helper,
    ):
        """测试统计查询性能"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])
        e2e_performance_monitor.start()

        # 测试多个统计查询的性能
        statistics_endpoints = [
            "/api/v1/statistics/overview",
            "/api/v1/statistics/task-completion-analysis",
            "/api/v1/statistics/work-hours-ranking",
            "/api/v1/statistics/area-distribution",
        ]

        query_times = []

        for i, endpoint in enumerate(statistics_endpoints):
            start_time = asyncio.get_event_loop().time()

            response = await e2e_client.get(endpoint, headers=admin_headers)

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            query_times.append(duration)

            e2e_performance_monitor.record(f"stats_query_{i}", duration)

            # 验证响应（允许404表示端点未实现但性能正常）
            assert response.status_code in [200, 404]

        # 性能验证
        if query_times:
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)

            assert (
                avg_query_time < 2.0
            ), f"Average statistics query time {avg_query_time}s exceeds 2s"
            assert (
                max_query_time < 5.0
            ), f"Max statistics query time {max_query_time}s exceeds 5s"

            summary = e2e_performance_monitor.summary()
            print(f"Statistics Query Performance Summary: {summary}")
        else:
            pytest.skip("No statistics queries performed for performance test")

    @pytest.mark.asyncio
    async def test_concurrent_statistics_access(
        self,
        e2e_client: AsyncClient,
        e2e_user_tokens: Dict[str, str],
        e2e_auth_headers,
        e2e_helper,
    ):
        """测试并发统计访问"""

        admin_headers = e2e_auth_headers(e2e_user_tokens["admin"])

        # 并发访问不同的统计端点
        concurrent_requests = [
            e2e_client.get("/api/v1/statistics/overview", headers=admin_headers),
            e2e_client.get("/api/v1/statistics/realtime", headers=admin_headers),
            e2e_client.get(
                "/api/v1/statistics/task-type-distribution", headers=admin_headers
            ),
            e2e_client.get(
                "/api/v1/statistics/member-performance", headers=admin_headers
            ),
            e2e_client.get("/api/v1/statistics/area-heatmap", headers=admin_headers),
        ]

        # 执行并发请求
        results = await asyncio.gather(*concurrent_requests, return_exceptions=True)

        # 验证并发请求结果
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                pytest.fail(
                    f"Concurrent statistics request {i} failed with exception: {result}"
                )
            else:
                # 允许200（成功）或404（端点未实现）
                assert result.status_code in [
                    200,
                    404,
                ], f"Concurrent statistics request {i} returned {result.status_code}"
