"""
测试统一消息管理系统
验证消息格式化和多语言支持是否正常工作
"""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "app"))

from app.core.exceptions import (
    AuthenticationError,
    ResourceNotFoundError,
    ValidationError,
)
from app.core.messages import (
    MessageFormatter,
    MessageManager,
    Messages,
    error_response,
    get_message,
    success_response,
)


def test_message_formatting():
    """测试消息格式化功能"""
    print("=== 测试消息格式化功能 ===")

    # 测试基本消息获取
    msg1 = get_message("AUTH_SUCCESS_LOGIN")
    print(f"基本消息: {msg1}")

    # 测试消息格式化
    msg2 = get_message("MEMBER_SUCCESS_LIST_RETRIEVE", total=150)
    print(f"格式化消息: {msg2}")

    # 测试复杂格式化
    msg3 = get_message("MEMBER_SUCCESS_CREATE", name="张三", student_id="2021001")
    print(f"复杂格式化: {msg3}")

    # 测试不存在的消息键
    msg4 = get_message("NON_EXISTENT_MESSAGE")
    print(f"不存在的消息键: {msg4}")

    print()


def test_response_creation():
    """测试响应创建功能"""
    print("=== 测试响应创建功能 ===")

    # 测试成功响应
    success_resp = success_response("AUTH_SUCCESS_LOGIN", data={"user_id": 1})
    print(f"成功响应: {success_resp}")

    # 测试错误响应
    error_resp = error_response("AUTH_ERROR_INVALID_CREDENTIALS")
    print(f"错误响应: {error_resp}")

    # 测试格式化响应
    member_resp = success_response(
        "MEMBER_SUCCESS_LIST_RETRIEVE", data={"items": [], "total": 0}, total=0
    )
    print(f"格式化响应: {member_resp}")

    print()


def test_exception_system():
    """测试异常系统"""
    print("=== 测试异常系统 ===")

    try:
        # 测试使用message_key的异常
        raise AuthenticationError(message_key="AUTH_ERROR_INVALID_CREDENTIALS")
    except AuthenticationError as e:
        print(f"认证异常: {e.message} (状态码: {e.status_code})")

    try:
        # 测试使用格式化参数的异常
        raise ValidationError(
            message_key="VALIDATION_ERROR_FIELD_REQUIRED", field="用户名"
        )
    except ValidationError as e:
        print(f"验证异常: {e.message} (状态码: {e.status_code})")

    try:
        # 测试传统方式（直接message）
        raise ResourceNotFoundError(message="自定义错误消息")
    except ResourceNotFoundError as e:
        print(f"资源不存在异常: {e.message} (状态码: {e.status_code})")

    print()


def test_message_consistency():
    """测试消息一致性"""
    print("=== 测试消息一致性 ===")

    # 检查关键消息是否存在
    critical_messages = [
        "AUTH_SUCCESS_LOGIN",
        "AUTH_ERROR_INVALID_CREDENTIALS",
        "MEMBER_SUCCESS_CREATE",
        "MEMBER_ERROR_NOT_FOUND",
        "TASK_SUCCESS_LIST_RETRIEVE",
        "VALIDATION_ERROR_GENERAL",
        "SYSTEM_ERROR_INTERNAL",
    ]

    for message_key in critical_messages:
        if hasattr(Messages, message_key):
            msg = getattr(Messages, message_key)
            print(f"✓ {message_key}: {msg}")
        else:
            print(f"✗ {message_key}: 消息不存在")

    print()


def test_message_manager():
    """测试消息管理器"""
    print("=== 测试消息管理器 ===")

    # 测试消息管理器的各种方法
    manager = MessageManager()

    success_msg = manager.get_message("AUTH_SUCCESS_LOGIN")
    print(f"消息管理器获取消息: {success_msg}")

    error_resp = manager.create_error_response("AUTH_ERROR_INVALID_CREDENTIALS")
    print(f"消息管理器创建错误响应: {error_resp}")

    success_resp = manager.create_success_response(
        "MEMBER_SUCCESS_LIST_RETRIEVE", data={"items": [], "total": 100}, total=100
    )
    print(f"消息管理器创建成功响应: {success_resp}")

    print()


if __name__ == "__main__":
    print("开始测试统一消息管理系统...\n")

    test_message_formatting()
    test_response_creation()
    test_exception_system()
    test_message_consistency()
    test_message_manager()

    print("✓ 统一消息管理系统测试完成")
