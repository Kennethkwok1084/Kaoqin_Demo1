"""
安全模块测试用例
测试密码哈希、JWT令牌、数据加密、权限验证、输入验证等安全功能
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock
import jwt
from jwt import PyJWTError
import secrets

from app.core.security import (
    create_access_token, create_refresh_token, verify_token,
    verify_password, get_password_hash, DataEncryption,
    encryption, encrypt_data, decrypt_data,
    generate_password_reset_token, verify_password_reset_token,
    generate_api_key, hash_api_key, verify_api_key,
    generate_session_id, generate_csrf_token, verify_csrf_token,
    get_security_headers, RateLimiter, rate_limiter,
    sanitize_input, validate_email_format, validate_phone_format,
    validate_password_strength, pwd_context
)
from app.core.config import settings


class TestJWTTokens:
    """测试JWT令牌功能"""

    def test_create_access_token_default_expiry(self):
        """测试创建访问令牌（默认过期时间）"""
        subject = "user123"
        token = create_access_token(subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌内容
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == subject
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_access_token_custom_expiry(self):
        """测试创建访问令牌（自定义过期时间）"""
        subject = "user456"
        expires_delta = timedelta(minutes=30)
        token = create_access_token(subject, expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + expires_delta
        
        # 允许几秒的误差
        assert abs(datetime.fromtimestamp(exp_timestamp).timestamp() - expected_exp.timestamp()) < 5

    def test_create_refresh_token_default_expiry(self):
        """测试创建刷新令牌（默认过期时间）"""
        subject = "user789"
        token = create_refresh_token(subject)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"

    def test_create_refresh_token_custom_expiry(self):
        """测试创建刷新令牌（自定义过期时间）"""
        subject = "user101"
        expires_delta = timedelta(days=7)
        token = create_refresh_token(subject, expires_delta)
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp_timestamp = payload["exp"]
        expected_exp = datetime.utcnow() + expires_delta
        
        # 允许几秒的误差
        assert abs(datetime.fromtimestamp(exp_timestamp).timestamp() - expected_exp.timestamp()) < 5

    def test_verify_token_valid_access_token(self):
        """测试验证有效的访问令牌"""
        subject = "user123"
        token = create_access_token(subject)
        
        payload = verify_token(token, "access")
        
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "access"

    def test_verify_token_valid_refresh_token(self):
        """测试验证有效的刷新令牌"""
        subject = "user123"
        token = create_refresh_token(subject)
        
        payload = verify_token(token, "refresh")
        
        assert payload is not None
        assert payload["sub"] == subject
        assert payload["type"] == "refresh"

    def test_verify_token_wrong_type(self):
        """测试验证错误类型的令牌"""
        subject = "user123"
        token = create_access_token(subject)
        
        # 尝试以刷新令牌验证访问令牌
        payload = verify_token(token, "refresh")
        assert payload is None

    def test_verify_token_expired(self):
        """测试验证过期令牌"""
        subject = "user123"
        # 创建一个已过期的令牌
        with patch('app.core.security.datetime') as mock_datetime:
            past_time = datetime.utcnow() - timedelta(hours=1)
            mock_datetime.utcnow.return_value = past_time
            mock_datetime.fromtimestamp = datetime.fromtimestamp
            
            token = create_access_token(subject, timedelta(minutes=1))
        
        payload = verify_token(token)
        assert payload is None

    def test_verify_token_invalid_signature(self):
        """测试验证签名无效的令牌"""
        # 创建一个使用错误密钥的令牌
        to_encode = {"exp": datetime.utcnow() + timedelta(minutes=30), "sub": "user123", "type": "access"}
        invalid_token = jwt.encode(to_encode, "wrong_secret_key", algorithm=settings.ALGORITHM)
        
        payload = verify_token(invalid_token)
        assert payload is None

    def test_verify_token_malformed(self):
        """测试验证格式错误的令牌"""
        malformed_token = "not.a.valid.jwt.token"
        
        payload = verify_token(malformed_token)
        assert payload is None

    def test_verify_token_missing_subject(self):
        """测试验证缺少subject的令牌"""
        to_encode = {"exp": datetime.utcnow() + timedelta(minutes=30), "type": "access"}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        payload = verify_token(token)
        assert payload is None

    def test_verify_token_missing_type(self):
        """测试验证缺少type的令牌"""
        to_encode = {"exp": datetime.utcnow() + timedelta(minutes=30), "sub": "user123"}
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        payload = verify_token(token)
        assert payload is None


class TestPasswordHashing:
    """测试密码哈希功能"""

    def test_get_password_hash(self):
        """测试密码哈希生成"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password  # 确保已加密
        assert hashed.startswith("$")  # bcrypt hash格式

    def test_verify_password_correct(self):
        """测试验证正确密码"""
        password = "TestPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试验证错误密码"""
        password = "TestPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """测试空密码验证"""
        password = ""
        hashed = get_password_hash("some_password")
        
        assert verify_password(password, hashed) is False

    def test_password_hash_uniqueness(self):
        """测试相同密码生成不同哈希"""
        password = "TestPassword123!"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)
        
        # bcrypt应该为相同密码生成不同的盐
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestDataEncryption:
    """测试数据加密功能"""

    def test_data_encryption_init(self):
        """测试数据加密初始化"""
        enc = DataEncryption()
        assert enc._cipher is not None

    def test_encrypt_decrypt_basic(self):
        """测试基本加密解密"""
        enc = DataEncryption()
        original_data = "Hello, World! 测试数据"
        
        encrypted = enc.encrypt(original_data)
        decrypted = enc.decrypt(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data

    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        enc = DataEncryption()
        empty_data = ""
        
        encrypted = enc.encrypt(empty_data)
        assert encrypted == empty_data  # 空字符串应该直接返回

    def test_decrypt_empty_string(self):
        """测试解密空字符串"""
        enc = DataEncryption()
        empty_data = ""
        
        decrypted = enc.decrypt(empty_data)
        assert decrypted == empty_data

    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        enc = DataEncryption()
        invalid_data = "invalid_encrypted_data"
        
        # 应该返回原始数据（向后兼容）
        result = enc.decrypt(invalid_data)
        assert result == invalid_data

    def test_encrypt_unicode_data(self):
        """测试加密Unicode数据"""
        enc = DataEncryption()
        unicode_data = "测试数据 🔒 العربية русский"
        
        encrypted = enc.encrypt(unicode_data)
        decrypted = enc.decrypt(encrypted)
        
        assert decrypted == unicode_data

    def test_global_encryption_functions(self):
        """测试全局加密函数"""
        original_data = "Global encryption test"
        
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        
        assert encrypted != original_data
        assert decrypted == original_data

    def test_encryption_consistency(self):
        """测试加密一致性（相同输入应产生不同输出）"""
        data = "Test data for consistency"
        
        encrypted1 = encrypt_data(data)
        encrypted2 = encrypt_data(data)
        
        # Fernet每次加密都会产生不同的密文
        assert encrypted1 != encrypted2
        assert decrypt_data(encrypted1) == data
        assert decrypt_data(encrypted2) == data


class TestPasswordResetTokens:
    """测试密码重置令牌"""

    def test_generate_password_reset_token(self):
        """测试生成密码重置令牌"""
        email = "test@example.com"
        token = generate_password_reset_token(email)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # 验证令牌内容
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email
        assert payload["type"] == "password_reset"

    def test_verify_password_reset_token_valid(self):
        """测试验证有效的密码重置令牌"""
        email = "test@example.com"
        token = generate_password_reset_token(email)
        
        verified_email = verify_password_reset_token(token)
        assert verified_email == email

    def test_verify_password_reset_token_invalid_type(self):
        """测试验证错误类型的令牌"""
        email = "test@example.com"
        # 创建访问令牌而不是密码重置令牌
        token = create_access_token(email)
        
        verified_email = verify_password_reset_token(token)
        assert verified_email is None

    def test_verify_password_reset_token_malformed(self):
        """测试验证格式错误的密码重置令牌"""
        malformed_token = "invalid.token"
        
        verified_email = verify_password_reset_token(malformed_token)
        assert verified_email is None

    def test_verify_password_reset_token_no_subject(self):
        """测试验证没有subject的密码重置令牌"""
        to_encode = {
            "exp": datetime.utcnow() + timedelta(hours=1),
            "type": "password_reset"
        }
        token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        verified_email = verify_password_reset_token(token)
        assert verified_email is None


class TestAPIKeys:
    """测试API密钥功能"""

    def test_generate_api_key(self):
        """测试生成API密钥"""
        api_key = generate_api_key()
        
        assert isinstance(api_key, str)
        assert len(api_key) > 0
        
        # URL安全的base64编码应该只包含特定字符
        import string
        allowed_chars = string.ascii_letters + string.digits + "-_"
        assert all(c in allowed_chars for c in api_key)

    def test_generate_api_key_uniqueness(self):
        """测试API密钥唯一性"""
        key1 = generate_api_key()
        key2 = generate_api_key()
        
        assert key1 != key2

    def test_hash_and_verify_api_key(self):
        """测试API密钥哈希和验证"""
        api_key = generate_api_key()
        hashed = hash_api_key(api_key)
        
        assert isinstance(hashed, str)
        assert hashed != api_key
        assert verify_api_key(api_key, hashed) is True

    def test_verify_api_key_incorrect(self):
        """测试验证错误的API密钥"""
        api_key = generate_api_key()
        wrong_key = generate_api_key()
        hashed = hash_api_key(api_key)
        
        assert verify_api_key(wrong_key, hashed) is False


class TestSessionAndCSRF:
    """测试会话和CSRF功能"""

    def test_generate_session_id(self):
        """测试生成会话ID"""
        session_id = generate_session_id()
        
        assert isinstance(session_id, str)
        assert len(session_id) > 0

    def test_generate_session_id_uniqueness(self):
        """测试会话ID唯一性"""
        id1 = generate_session_id()
        id2 = generate_session_id()
        
        assert id1 != id2

    def test_generate_csrf_token(self):
        """测试生成CSRF令牌"""
        csrf_token = generate_csrf_token()
        
        assert isinstance(csrf_token, str)
        assert len(csrf_token) > 0

    def test_verify_csrf_token_correct(self):
        """测试验证正确的CSRF令牌"""
        token = generate_csrf_token()
        
        assert verify_csrf_token(token, token) is True

    def test_verify_csrf_token_incorrect(self):
        """测试验证错误的CSRF令牌"""
        token1 = generate_csrf_token()
        token2 = generate_csrf_token()
        
        assert verify_csrf_token(token1, token2) is False


class TestSecurityHeaders:
    """测试安全头功能"""

    def test_get_security_headers_enabled(self):
        """测试安全头启用时"""
        with patch.object(settings, 'SECURITY_HEADERS_ENABLED', True), \
             patch.object(settings, 'CSP_POLICY', "default-src 'self'"):
            
            headers = get_security_headers()
            
            assert isinstance(headers, dict)
            assert "X-Content-Type-Options" in headers
            assert "X-Frame-Options" in headers
            assert "X-XSS-Protection" in headers
            assert "Strict-Transport-Security" in headers
            assert "Content-Security-Policy" in headers
            assert "Referrer-Policy" in headers
            assert "Permissions-Policy" in headers

    def test_get_security_headers_disabled(self):
        """测试安全头禁用时"""
        with patch.object(settings, 'SECURITY_HEADERS_ENABLED', False):
            headers = get_security_headers()
            assert headers == {}

    def test_security_headers_values(self):
        """测试安全头值"""
        with patch.object(settings, 'SECURITY_HEADERS_ENABLED', True), \
             patch.object(settings, 'CSP_POLICY', "default-src 'self'"):
            
            headers = get_security_headers()
            
            assert headers["X-Content-Type-Options"] == "nosniff"
            assert headers["X-Frame-Options"] == "DENY"
            assert headers["Content-Security-Policy"] == "default-src 'self'"


class TestRateLimiter:
    """测试限流器功能"""

    def test_rate_limiter_init(self):
        """测试限流器初始化"""
        limiter = RateLimiter()
        assert limiter._requests == {}

    def test_rate_limiter_allow_first_request(self):
        """测试限流器允许首次请求"""
        limiter = RateLimiter()
        
        allowed = limiter.is_allowed("user1", max_requests=5, window_seconds=60)
        assert allowed is True

    def test_rate_limiter_allow_within_limit(self):
        """测试限流器在限制内允许请求"""
        limiter = RateLimiter()
        
        # 连续5个请求都应该被允许
        for i in range(5):
            allowed = limiter.is_allowed("user1", max_requests=5, window_seconds=60)
            assert allowed is True

    def test_rate_limiter_deny_over_limit(self):
        """测试限流器拒绝超限请求"""
        limiter = RateLimiter()
        
        # 前5个请求应该被允许
        for i in range(5):
            limiter.is_allowed("user1", max_requests=5, window_seconds=60)
        
        # 第6个请求应该被拒绝
        allowed = limiter.is_allowed("user1", max_requests=5, window_seconds=60)
        assert allowed is False

    def test_rate_limiter_different_users(self):
        """测试不同用户的独立限制"""
        limiter = RateLimiter()
        
        # 用户1达到限制
        for i in range(5):
            limiter.is_allowed("user1", max_requests=5, window_seconds=60)
        
        # 用户2仍应被允许
        allowed = limiter.is_allowed("user2", max_requests=5, window_seconds=60)
        assert allowed is True

    def test_rate_limiter_window_cleanup(self):
        """测试限流器时间窗口清理"""
        limiter = RateLimiter()
        
        with patch('app.core.security.datetime') as mock_datetime:
            # 模拟当前时间
            now = datetime.utcnow()
            mock_datetime.utcnow.return_value = now
            
            # 发送请求
            limiter.is_allowed("user1", max_requests=1, window_seconds=60)
            
            # 模拟时间过去
            mock_datetime.utcnow.return_value = now + timedelta(seconds=61)
            
            # 应该允许新请求（旧请求已过期）
            allowed = limiter.is_allowed("user1", max_requests=1, window_seconds=60)
            assert allowed is True

    def test_global_rate_limiter(self):
        """测试全局限流器实例"""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)


class TestInputValidation:
    """测试输入验证功能"""

    def test_sanitize_input_basic(self):
        """测试基本输入清理"""
        dangerous_input = "<script>alert('xss')</script>"
        sanitized = sanitize_input(dangerous_input)
        
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
        assert "alert(&#x27;xss&#x27;)" in sanitized

    def test_sanitize_input_empty(self):
        """测试清理空输入"""
        empty_input = ""
        sanitized = sanitize_input(empty_input)
        assert sanitized == empty_input

    def test_sanitize_input_none(self):
        """测试清理None输入"""
        sanitized = sanitize_input(None)
        assert sanitized is None

    def test_sanitize_input_html_entities(self):
        """测试HTML实体清理"""
        test_cases = [
            ("&", "&amp;"),
            ("<", "&lt;"),
            (">", "&gt;"),
            ('"', "&quot;"),
            ("'", "&#x27;"),
            ("/", "&#x2F;"),
        ]
        
        for original, expected in test_cases:
            sanitized = sanitize_input(original)
            assert expected in sanitized

    def test_validate_email_format_valid(self):
        """测试有效邮箱格式验证"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@domain.com",
        ]
        
        for email in valid_emails:
            assert validate_email_format(email) is True

    def test_validate_email_format_invalid(self):
        """测试无效邮箱格式验证"""
        invalid_emails = [
            "invalid.email",
            "@domain.com",
            "user@",
            "user@@domain.com",
            "user@domain",
            "",
        ]
        
        for email in invalid_emails:
            assert validate_email_format(email) is False

    def test_validate_phone_format_valid(self):
        """测试有效手机号格式验证"""
        valid_phones = [
            "13812345678",
            "15987654321",
            "18611112222",
            "19999888777",
        ]
        
        for phone in valid_phones:
            assert validate_phone_format(phone) is True

    def test_validate_phone_format_invalid(self):
        """测试无效手机号格式验证"""
        invalid_phones = [
            "12812345678",  # 不是1[3-9]开头
            "1381234567",   # 长度不够
            "138123456789", # 长度过长
            "13a12345678",  # 包含字母
            "",             # 空字符串
        ]
        
        for phone in invalid_phones:
            assert validate_phone_format(phone) is False


class TestPasswordStrengthValidation:
    """测试密码强度验证"""

    def test_validate_password_strength_strong(self):
        """测试强密码验证"""
        strong_password = "StrongP@ssw0rd123"
        is_valid, errors = validate_password_strength(strong_password)
        
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_password_strength_too_short(self):
        """测试过短密码验证"""
        short_password = "Abc1!"
        is_valid, errors = validate_password_strength(short_password)
        
        assert is_valid is False
        assert "密码长度至少8个字符" in errors

    def test_validate_password_strength_no_uppercase(self):
        """测试缺少大写字母的密码"""
        password = "weakpassword123!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert "密码必须包含至少一个大写字母" in errors

    def test_validate_password_strength_no_lowercase(self):
        """测试缺少小写字母的密码"""
        password = "WEAKPASSWORD123!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert "密码必须包含至少一个小写字母" in errors

    def test_validate_password_strength_no_digit(self):
        """测试缺少数字的密码"""
        password = "WeakPassword!"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert "密码必须包含至少一个数字" in errors

    def test_validate_password_strength_no_special(self):
        """测试缺少特殊字符的密码"""
        password = "WeakPassword123"
        is_valid, errors = validate_password_strength(password)
        
        assert is_valid is False
        assert "密码必须包含至少一个特殊字符" in errors

    def test_validate_password_strength_multiple_errors(self):
        """测试多个错误的弱密码"""
        weak_password = "weak"
        is_valid, errors = validate_password_strength(weak_password)
        
        assert is_valid is False
        assert len(errors) == 5  # 所有验证规则都应该失败


class TestSecurityIntegration:
    """测试安全功能集成"""

    def test_jwt_and_password_integration(self):
        """测试JWT和密码功能集成"""
        # 模拟用户注册和登录流程
        password = "UserPassword123!"
        hashed_password = get_password_hash(password)
        
        # 验证密码
        assert verify_password(password, hashed_password) is True
        
        # 创建令牌
        user_id = "123"
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)
        
        # 验证令牌
        access_payload = verify_token(access_token, "access")
        refresh_payload = verify_token(refresh_token, "refresh")
        
        assert access_payload["sub"] == user_id
        assert refresh_payload["sub"] == user_id

    def test_encryption_and_validation_integration(self):
        """测试加密和验证功能集成"""
        # 模拟敏感数据处理
        email = "user@example.com"
        phone = "13812345678"
        
        # 验证格式
        assert validate_email_format(email) is True
        assert validate_phone_format(phone) is True
        
        # 清理和加密
        sanitized_email = sanitize_input(email)
        encrypted_phone = encrypt_data(phone)
        
        # 解密验证
        decrypted_phone = decrypt_data(encrypted_phone)
        assert decrypted_phone == phone

    def test_api_key_and_rate_limiting_integration(self):
        """测试API密钥和限流集成"""
        # 生成和验证API密钥
        api_key = generate_api_key()
        hashed_key = hash_api_key(api_key)
        assert verify_api_key(api_key, hashed_key) is True
        
        # 测试限流
        limiter = RateLimiter()
        for i in range(3):
            allowed = limiter.is_allowed(api_key, max_requests=3, window_seconds=60)
            assert allowed is True
        
        # 超限请求
        over_limit = limiter.is_allowed(api_key, max_requests=3, window_seconds=60)
        assert over_limit is False


class TestSecurityConfiguration:
    """测试安全配置"""

    def test_password_context_configuration(self):
        """测试密码上下文配置"""
        assert pwd_context is not None
        
        # 测试基本功能
        password = "TestPassword123!"
        hashed = pwd_context.hash(password)
        assert pwd_context.verify(password, hashed) is True

    def test_encryption_instance(self):
        """测试全局加密实例"""
        assert encryption is not None
        assert isinstance(encryption, DataEncryption)

    def test_rate_limiter_instance(self):
        """测试全局限流器实例"""
        assert rate_limiter is not None
        assert isinstance(rate_limiter, RateLimiter)


class TestSecurityEdgeCases:
    """测试安全功能边界情况"""

    def test_jwt_with_numeric_subject(self):
        """测试数字主题的JWT令牌"""
        numeric_subject = 12345
        token = create_access_token(numeric_subject)
        
        payload = verify_token(token)
        assert payload is not None
        assert payload["sub"] == str(numeric_subject)  # 应该转换为字符串

    def test_encryption_with_special_characters(self):
        """测试加密特殊字符"""
        special_data = "!@#$%^&*()_+{}|:<>?[]\\;'\",./"
        encrypted = encrypt_data(special_data)
        decrypted = decrypt_data(encrypted)
        
        assert decrypted == special_data

    def test_rate_limiter_zero_requests(self):
        """测试限流器零请求限制"""
        limiter = RateLimiter()
        
        # 零请求限制应该立即拒绝
        allowed = limiter.is_allowed("user1", max_requests=0, window_seconds=60)
        assert allowed is False

    def test_sanitize_input_mixed_content(self):
        """测试清理混合内容"""
        mixed_input = "Normal text <script>evil</script> & more text"
        sanitized = sanitize_input(mixed_input)
        
        assert "Normal text" in sanitized
        assert "&lt;script&gt;" in sanitized
        assert "&amp;" in sanitized

    def test_password_strength_edge_cases(self):
        """测试密码强度边界情况"""
        # 最小强密码
        minimal_strong = "Aa1!bcde"
        is_valid, errors = validate_password_strength(minimal_strong)
        assert is_valid is True
        
        # 空密码
        empty_password = ""
        is_valid, errors = validate_password_strength(empty_password)
        assert is_valid is False
        assert len(errors) > 0


class TestSecurityPerformance:
    """测试安全功能性能"""

    def test_password_hashing_performance(self):
        """测试密码哈希性能"""
        password = "TestPassword123!"
        
        # 哈希应该相对较快
        import time
        start_time = time.time()
        hashed = get_password_hash(password)
        end_time = time.time()
        
        # 哈希时间应该在合理范围内（通常小于1秒）
        hash_time = end_time - start_time
        assert hash_time < 1.0
        
        # 验证也应该快速
        start_time = time.time()
        verify_password(password, hashed)
        end_time = time.time()
        
        verify_time = end_time - start_time
        assert verify_time < 0.5

    def test_encryption_performance(self):
        """测试加密性能"""
        large_data = "A" * 10000  # 10KB数据
        
        import time
        start_time = time.time()
        encrypted = encrypt_data(large_data)
        decrypted = decrypt_data(encrypted)
        end_time = time.time()
        
        # 加解密时间应该在合理范围内
        crypto_time = end_time - start_time
        assert crypto_time < 1.0
        assert decrypted == large_data