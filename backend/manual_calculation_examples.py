#!/usr/bin/env python3
"""
手动计算示例 - 用于验证工时算法的正确性
提供具体的计算案例，确保算法实现与业务规则一致
"""

def manual_work_hours_examples():
    """
    手动计算示例 - 基于 CLAUDE.md 中的工时规则

    工时规则:
    - 线上任务: 40分钟
    - 线下任务: 100分钟
    - 加急奖励: +15分钟
    - 非默认好评奖励: +30分钟
    - 响应超时惩罚: -30分钟
    - 完成超时惩罚: -30分钟
    - 差评惩罚: -60分钟
    - 工时最低值: 0分钟 (不能为负)
    """

    print("📝 工时计算手动验证示例")
    print("=" * 50)
    print("目标: 验证系统计算结果与手动计算是否一致")
    print()

    examples = [
        {
            "name": "示例1: 普通线上维修任务",
            "description": "最简单的基础案例",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟",
            "expected_minutes": 40,
            "expected_hours": 0.67
        },

        {
            "name": "示例2: 普通线下维修任务",
            "description": "线下任务基础工时更高",
            "conditions": {
                "task_type": "repair",
                "is_online": False,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 100分钟",
            "expected_minutes": 100,
            "expected_hours": 1.67
        },

        {
            "name": "示例3: 线上加急任务",
            "description": "加急任务获得奖励",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": True,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 + 加急奖励: 15分钟 = 55分钟",
            "expected_minutes": 55,
            "expected_hours": 0.92
        },

        {
            "name": "示例4: 线上好评任务",
            "description": "非默认好评获得奖励",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": True,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 + 好评奖励: 30分钟 = 70分钟",
            "expected_minutes": 70,
            "expected_hours": 1.17
        },

        {
            "name": "示例5: 线下加急好评任务",
            "description": "多重奖励叠加的最佳情况",
            "conditions": {
                "task_type": "repair",
                "is_online": False,
                "is_rush": True,
                "positive_review": True,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 100分钟 + 加急奖励: 15分钟 + 好评奖励: 30分钟 = 145分钟",
            "expected_minutes": 145,
            "expected_hours": 2.42
        },

        {
            "name": "示例6: 响应超时任务",
            "description": "响应超时会被扣分",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": True,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 - 响应超时惩罚: 30分钟 = 10分钟",
            "expected_minutes": 10,
            "expected_hours": 0.17
        },

        {
            "name": "示例7: 完成超时任务",
            "description": "完成超时会被扣分",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": True,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 - 完成超时惩罚: 30分钟 = 10分钟",
            "expected_minutes": 10,
            "expected_hours": 0.17
        },

        {
            "name": "示例8: 双重超时惩罚",
            "description": "响应和完成都超时",
            "conditions": {
                "task_type": "repair",
                "is_online": False,
                "is_rush": False,
                "positive_review": False,
                "late_response": True,
                "late_completion": True,
                "negative_review": False
            },
            "calculation": "基础工时: 100分钟 - 响应超时: 30分钟 - 完成超时: 30分钟 = 40分钟",
            "expected_minutes": 40,
            "expected_hours": 0.67
        },

        {
            "name": "示例9: 差评任务",
            "description": "差评惩罚最重",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": True
            },
            "calculation": "基础工时: 40分钟 - 差评惩罚: 60分钟 = -20分钟 → 保护为 0分钟",
            "expected_minutes": 0,
            "expected_hours": 0.0
        },

        {
            "name": "示例10: 极端惩罚情况",
            "description": "所有惩罚叠加的最坏情况",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": True,
                "late_completion": True,
                "negative_review": True
            },
            "calculation": "基础工时: 40分钟 - 响应超时: 30分钟 - 完成超时: 30分钟 - 差评: 60分钟 = -80分钟 → 保护为 0分钟",
            "expected_minutes": 0,
            "expected_hours": 0.0
        },

        {
            "name": "示例11: 奖惩抵消",
            "description": "加急任务但响应超时",
            "conditions": {
                "task_type": "repair",
                "is_online": True,
                "is_rush": True,
                "positive_review": False,
                "late_response": True,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 + 加急奖励: 15分钟 - 响应超时: 30分钟 = 25分钟",
            "expected_minutes": 25,
            "expected_hours": 0.42
        },

        {
            "name": "示例12: 协助任务 (自定义时长)",
            "description": "协助任务使用自定义时长",
            "conditions": {
                "task_type": "assistance",
                "custom_minutes": 90,
                "is_online": None,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "自定义工时: 90分钟",
            "expected_minutes": 90,
            "expected_hours": 1.5
        },

        {
            "name": "示例13: 协助任务 (零时长)",
            "description": "协助任务可以设置为0",
            "conditions": {
                "task_type": "assistance",
                "custom_minutes": 0,
                "is_online": None,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "自定义工时: 0分钟",
            "expected_minutes": 0,
            "expected_hours": 0.0
        },

        {
            "name": "示例14: 监控任务",
            "description": "监控任务按线上任务计算",
            "conditions": {
                "task_type": "monitoring",
                "is_online": True,
                "is_rush": False,
                "positive_review": False,
                "late_response": False,
                "late_completion": False,
                "negative_review": False
            },
            "calculation": "基础工时: 40分钟 (按线上任务计算)",
            "expected_minutes": 40,
            "expected_hours": 0.67
        }
    ]

    print("📊 计算示例清单:")
    print("-" * 50)

    for i, example in enumerate(examples, 1):
        print(f"\n{i:2d}. {example['name']}")
        print(f"    描述: {example['description']}")
        print(f"    计算: {example['calculation']}")
        print(f"    期望: {example['expected_minutes']}分钟 ({example['expected_hours']:.2f}小时)")

        # 打印条件
        conditions = example['conditions']
        condition_str = []
        if conditions.get('is_online') is not None:
            condition_str.append(f"{'线上' if conditions['is_online'] else '线下'}")
        if conditions.get('is_rush'):
            condition_str.append("加急")
        if conditions.get('positive_review'):
            condition_str.append("好评")
        if conditions.get('late_response'):
            condition_str.append("响应超时")
        if conditions.get('late_completion'):
            condition_str.append("完成超时")
        if conditions.get('negative_review'):
            condition_str.append("差评")
        if conditions.get('custom_minutes') is not None:
            condition_str.append(f"自定义{conditions['custom_minutes']}分钟")

        if condition_str:
            print(f"    条件: {', '.join(condition_str)}")

    print("\n" + "=" * 50)
    print("💡 验证方法:")
    print("1. 在系统中创建相应条件的任务")
    print("2. 完成任务并触发工时计算")
    print("3. 检查计算结果是否与期望值一致")
    print("4. 任何差异都表示算法实现有误")
    print()
    print("⚠️  注意: 算法准确性是上线的绝对底线!")

    return examples

def verify_calculation_logic():
    """验证计算逻辑的一致性"""
    print("\n🔍 计算逻辑验证")
    print("-" * 30)

    # 基础规则
    ONLINE_MINUTES = 40
    OFFLINE_MINUTES = 100
    RUSH_BONUS = 15
    POSITIVE_REVIEW_BONUS = 30
    LATE_RESPONSE_PENALTY = -30
    LATE_COMPLETION_PENALTY = -30
    NEGATIVE_REVIEW_PENALTY = -60

    print("📋 工时计算规则:")
    print(f"  • 线上任务: {ONLINE_MINUTES}分钟")
    print(f"  • 线下任务: {OFFLINE_MINUTES}分钟")
    print(f"  • 加急奖励: +{RUSH_BONUS}分钟")
    print(f"  • 好评奖励: +{POSITIVE_REVIEW_BONUS}分钟")
    print(f"  • 响应超时惩罚: {LATE_RESPONSE_PENALTY}分钟")
    print(f"  • 完成超时惩罚: {LATE_COMPLETION_PENALTY}分钟")
    print(f"  • 差评惩罚: {NEGATIVE_REVIEW_PENALTY}分钟")
    print(f"  • 最低工时: 0分钟 (不能为负)")

    print("\n🧮 计算公式:")
    print("工时 = 基础工时 + 奖励总和 + 惩罚总和")
    print("最终工时 = max(0, 工时)")

    print("\n📝 边界条件:")
    print("1. 协助任务使用自定义时长，不受其他规则影响")
    print("2. 监控任务按线上任务规则计算")
    print("3. 工时结果四舍五入到小数点后2位")
    print("4. 所有惩罚可以叠加，但总工时不能为负数")

def calculate_expected_work_hours(task_type, is_online=True, is_rush=False,
                                positive_review=False, late_response=False,
                                late_completion=False, negative_review=False,
                                custom_minutes=None):
    """
    计算期望工时 - 用于验证系统计算结果
    """
    if task_type == "assistance" and custom_minutes is not None:
        return max(0, custom_minutes)

    # 基础工时
    base_minutes = 40 if is_online else 100

    # 奖励
    bonus = 0
    if is_rush:
        bonus += 15
    if positive_review:
        bonus += 30

    # 惩罚
    penalty = 0
    if late_response:
        penalty -= 30
    if late_completion:
        penalty -= 30
    if negative_review:
        penalty -= 60

    # 总工时
    total_minutes = base_minutes + bonus + penalty

    # 不能为负
    return max(0, total_minutes)

if __name__ == "__main__":
    # 显示所有手动计算示例
    examples = manual_work_hours_examples()

    # 验证计算逻辑
    verify_calculation_logic()

    print(f"\n📈 总计 {len(examples)} 个验证案例")
    print("建议在系统中逐一验证这些案例的计算结果")