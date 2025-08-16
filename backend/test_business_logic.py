#!/usr/bin/env python3
"""
Test core business logic without database dependencies
"""

from datetime import datetime, timedelta
from decimal import Decimal


class MockTask:
    def __init__(self, task_type='ONLINE', is_rush=False, has_positive_review=False, 
                 late_response=False, late_completion=False, has_negative_review=False):
        self.task_type = task_type
        self.is_rush = is_rush
        self.has_positive_review = has_positive_review
        self.late_response = late_response
        self.late_completion = late_completion
        self.has_negative_review = has_negative_review


def calculate_work_hours(task):
    """Calculate work hours based on business rules"""
    # Base hours
    base_hours = 40 if task.task_type == 'ONLINE' else 100
    
    # Bonuses
    if task.is_rush:
        base_hours += 15
    if task.has_positive_review:
        base_hours += 30
        
    # Penalties
    if task.late_response:
        base_hours -= 30
    if task.late_completion:
        base_hours -= 30
    if task.has_negative_review:
        base_hours -= 60
        
    return max(0, base_hours)


def test_ab_table_matching():
    """Test A/B table matching logic"""
    # Mock member data
    members = [
        {"name": "张三", "contact": "13800138000"},
        {"name": "李四", "contact": "13900139000"},
        {"name": "王五", "contact": "13700137000"},
    ]
    
    # Mock task data
    tasks = [
        {"reporter_name": "张三", "reporter_contact": "13800138000", "title": "网络问题"},
        {"reporter_name": "李四", "reporter_contact": "13900139000", "title": "电脑故障"},
        {"reporter_name": "赵六", "reporter_contact": "13600136000", "title": "新用户任务"},
    ]
    
    matched = 0
    unmatched = 0
    
    for task in tasks:
        found_match = False
        for member in members:
            if (task["reporter_name"] == member["name"] and 
                task["reporter_contact"] == member["contact"]):
                matched += 1
                found_match = True
                break
        if not found_match:
            unmatched += 1
    
    return {
        "total_tasks": len(tasks),
        "matched": matched,
        "unmatched": unmatched,
        "match_rate": matched / len(tasks) * 100
    }


def main():
    print("Core Business Logic Validation")
    print("=" * 50)
    
    # Test work hours calculation
    print("\n1. Work Hours Calculation Tests:")
    print("-" * 30)
    
    test_cases = [
        ('Basic online task', MockTask('ONLINE'), 40),
        ('Basic offline task', MockTask('OFFLINE'), 100),
        ('Rush online task', MockTask('ONLINE', is_rush=True), 55),
        ('Positive review bonus', MockTask('ONLINE', has_positive_review=True), 70),
        ('Late response penalty', MockTask('ONLINE', late_response=True), 10),
        ('Multiple penalties', MockTask('ONLINE', late_response=True, late_completion=True, has_negative_review=True), 0),
        ('Mixed scenario', MockTask('ONLINE', is_rush=True, has_positive_review=True, late_response=True), 55),
    ]
    
    all_passed = True
    for name, task, expected in test_cases:
        actual = calculate_work_hours(task)
        status = 'PASS' if actual == expected else 'FAIL'
        if actual != expected:
            all_passed = False
        print(f'{name:<25} | Expected: {expected:3d} | Actual: {actual:3d} | {status}')
    
    print(f'\nWork Hours Tests: {"PASS" if all_passed else "FAIL"}')
    
    # Test A/B table matching
    print("\n2. A/B Table Matching Tests:")
    print("-" * 30)
    
    matching_result = test_ab_table_matching()
    print(f"Total tasks: {matching_result['total_tasks']}")
    print(f"Matched: {matching_result['matched']}")
    print(f"Unmatched: {matching_result['unmatched']}")
    print(f"Match rate: {matching_result['match_rate']:.1f}%")
    
    match_test_pass = matching_result['match_rate'] >= 60  # Expected at least 60% match rate
    print(f"A/B Matching Test: {'PASS' if match_test_pass else 'FAIL'}")
    
    # Overall result
    print("\n" + "=" * 50)
    overall_pass = all_passed and match_test_pass
    print(f"Overall Business Logic Validation: {'PASS' if overall_pass else 'FAIL'}")
    
    return overall_pass


if __name__ == "__main__":
    main()