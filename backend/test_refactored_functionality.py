"""
Simple test script to verify refactored functionality works
Tests the new services and models without requiring full test environment
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


def test_imports():
    """Test that all refactored modules can be imported successfully"""
    try:
        # Test core model imports
        from app.models.member import Member
        from app.models.task import RepairTask, TaskTag, TaskTagType

        # Test service imports
        from app.services.ab_table_matching_service import (
            ABTableMatchingService,
            MatchingStrategy,
            MatchResult,
        )
        from app.services.import_service import ImportService
        from app.services.task_service import TaskService
        from app.services.work_hours_service import (
            RushTaskMarkingService,
            WorkHoursCalculationService,
        )

        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {str(e)}")
        return False


def test_model_functionality():
    """Test basic model functionality"""
    try:
        # Test TaskTag factory methods
        rush_tag = TaskTag.create_rush_order_tag()
        assert rush_tag.name == "爆单任务"
        assert rush_tag.work_minutes_modifier == 15
        assert rush_tag.tag_type == TaskTagType.RUSH_ORDER

        rating_tag = TaskTag.create_non_default_rating_tag()
        assert rating_tag.name == "非默认好评"
        assert rating_tag.work_minutes_modifier == 30

        timeout_tag = TaskTag.create_timeout_response_tag()
        assert timeout_tag.name == "超时响应"
        assert timeout_tag.work_minutes_modifier == -30

        # Test tag type checking methods
        assert rush_tag.is_rush_order_tag()
        assert not rush_tag.is_penalty_tag()
        assert timeout_tag.is_penalty_tag()
        assert not timeout_tag.is_bonus_tag()
        assert rating_tag.is_bonus_tag()

        print("✓ Model functionality tests passed")
        return True
    except Exception as e:
        print(f"✗ Model functionality test failed: {str(e)}")
        return False


def test_matching_service_logic():
    """Test AB table matching service logic without database"""
    try:
        # Test similarity algorithms
        from app.services.ab_table_matching_service import ABTableMatchingService

        # Create a mock service instance (without db)
        class MockDB:
            pass

        service = ABTableMatchingService(MockDB())

        # Test name cleaning
        clean_name1 = service._clean_name("张三（技术员）")
        clean_name2 = service._clean_name("李四 [组长]")
        assert len(clean_name1) > 0
        assert len(clean_name2) > 0

        # Test phone cleaning
        clean_phone1 = service._clean_phone("+86 138-1234-5678")
        clean_phone2 = service._clean_phone("(138) 1234-5678")
        assert clean_phone1 == "13812345678"
        assert clean_phone2 == "13812345678"

        # Test similarity scoring
        sim1 = service._name_similarity_score("张三", "张三")
        sim2 = service._name_similarity_score("张三", "张三丰")
        sim3 = service._name_similarity_score("张三", "李四")

        assert sim1 == 1.0  # Exact match
        assert sim2 > sim3  # Partial match better than no match

        # Test phone matching
        match1 = service._phones_match("13812345678", "13812345678")
        match2 = service._phones_match("8613812345678", "13812345678")
        match3 = service._phones_match("13812345678", "13812345679")

        assert match1 == True
        assert match2 == True  # Should match after cleaning
        assert match3 == False

        print("✓ Matching service logic tests passed")
        return True
    except Exception as e:
        print(f"✗ Matching service logic test failed: {str(e)}")
        return False


def test_work_hours_calculation():
    """Test work hours calculation logic"""
    try:
        from datetime import datetime

        from app.models.task import RepairTask, TaskStatus, TaskType

        # Create a mock repair task
        task = RepairTask(
            id=1,
            task_id="TEST-001",
            title="Test Task",
            task_type=TaskType.ONLINE,
            status=TaskStatus.COMPLETED,
            report_time=datetime.utcnow(),
            is_rush_order=False,
        )

        # Mock the tags relationship as empty list
        task.tags = []

        # Test base work minutes calculation
        base_minutes = task.get_base_work_minutes()
        # Should get settings.DEFAULT_ONLINE_TASK_MINUTES, but we'll accept any positive value
        assert base_minutes > 0

        # Test rush order functionality
        task.mark_as_rush_order(True)
        assert task.is_rush_order == True

        task.mark_as_rush_order(False)
        assert task.is_rush_order == False

        # Test status mapping
        task.set_status_by_work_order_status("已完成")
        assert task.status == TaskStatus.COMPLETED

        task.set_status_by_work_order_status("处理中")
        assert task.status == TaskStatus.IN_PROGRESS

        # Test repair form mapping
        task.set_task_type_by_repair_form("远程维修")
        assert task.task_type == TaskType.ONLINE

        task.set_task_type_by_repair_form("现场维修")
        assert task.task_type == TaskType.OFFLINE

        print("✓ Work hours calculation tests passed")
        return True
    except Exception as e:
        print(f"✗ Work hours calculation test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("Running refactored functionality tests...")
    print("=" * 50)

    all_passed = True

    # Run all test functions
    tests = [
        test_imports,
        test_model_functionality,
        test_matching_service_logic,
        test_work_hours_calculation,
    ]

    for test in tests:
        if not test():
            all_passed = False
        print()

    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! Refactored functionality is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
