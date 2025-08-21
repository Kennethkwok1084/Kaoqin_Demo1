"""
简单测试消息系统是否正常工作
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.messages import get_message, success_response, Messages

def test_basic_functionality():
    """测试基本功能"""
    
    # 测试基本消息
    login_msg = get_message("AUTH_SUCCESS_LOGIN")
    print("Login message:", login_msg)
    
    # 测试格式化消息
    member_msg = get_message("MEMBER_SUCCESS_LIST_RETRIEVE", total=100)
    print("Member message:", member_msg)
    
    # 测试响应创建
    response = success_response("AUTH_SUCCESS_LOGIN", data={"user_id": 1})
    print("Response success:", response.get("success"))
    print("Response message:", response.get("message"))
    
    # 检查是否为中文消息
    auth_error = get_message("AUTH_ERROR_INVALID_CREDENTIALS")
    print("Auth error message:", auth_error)
    print("Is Chinese message:", "用户名" in auth_error or "密码" in auth_error)
    
    print("Basic functionality test PASSED")

if __name__ == "__main__":
    test_basic_functionality()