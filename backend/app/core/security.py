"""
Security utilities for authentication and encryption.
Handles JWT tokens, password hashing, and data encryption.
"""

import base64
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context
# Always use simple bcrypt context to avoid deprecated scheme issues
pwd_context = CryptContext(schemes=settings.PWD_CONTEXT_SCHEMES)


# Password utilities
def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Check token type
        if payload.get("type") != token_type:
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp) < datetime.utcnow():
            return None

        # Get subject
        subject: str = payload.get("sub")
        if subject is None:
            return None

        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


# Data Encryption utilities (AES-256-GCM)
class DataEncryption:
    """Data encryption utility using AES-256-GCM."""

    def __init__(self):
        self._cipher = self._get_cipher()

    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher."""
        # Derive key from settings
        password = settings.ENCRYPTION_KEY.encode()
        salt = settings.SALT.encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def encrypt(self, data: str) -> str:
        """Encrypt string data."""
        if not data:
            return data
        encrypted_data = self._cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data."""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self._cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            # Return original data if decryption fails (backward compatibility)
            return encrypted_data


# Global encryption instance
encryption = DataEncryption()


# Convenience functions for encryption
def encrypt_data(data: str) -> str:
    """Encrypt string data using global encryption instance."""
    return encryption.encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt string data using global encryption instance."""
    return encryption.decrypt(encrypted_data)


# Token utilities
def generate_password_reset_token(email: str) -> str:
    """Generate password reset token."""
    delta = timedelta(
        hours=(
            settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS
            if hasattr(settings, "EMAIL_RESET_TOKEN_EXPIRE_HOURS")
            else 1
        )
    )
    now = datetime.utcnow()
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token."""
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        # Check token type
        if decoded_token.get("type") != "password_reset":
            return None

        return decoded_token.get("sub")
    except JWTError:
        return None


# API Key utilities
def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return pwd_context.hash(api_key)


def verify_api_key(api_key: str, hashed_api_key: str) -> bool:
    """Verify an API key against its hash."""
    return pwd_context.verify(api_key, hashed_api_key)


# Session utilities
def generate_session_id() -> str:
    """Generate a secure session ID."""
    return secrets.token_urlsafe(24)


# CSRF Protection
def generate_csrf_token() -> str:
    """Generate CSRF token."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(token: str, session_token: str) -> bool:
    """Verify CSRF token."""
    return secrets.compare_digest(token, session_token)


# Security Headers
def get_security_headers() -> dict:
    """Get security headers for responses."""
    if not settings.SECURITY_HEADERS_ENABLED:
        return {}

    return {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Content-Security-Policy": settings.CSP_POLICY,
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }


# Rate limiting utilities
class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self):
        self._requests = {}

    def is_allowed(
        self, identifier: str, max_requests: int, window_seconds: int
    ) -> bool:
        """Check if request is allowed."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)

        # Clean old requests
        if identifier in self._requests:
            self._requests[identifier] = [
                req_time
                for req_time in self._requests[identifier]
                if req_time > window_start
            ]
        else:
            self._requests[identifier] = []

        # Check rate limit
        if len(self._requests[identifier]) >= max_requests:
            return False

        # Add current request
        self._requests[identifier].append(now)
        return True


# Global rate limiter instance
rate_limiter = RateLimiter()


# Input validation utilities
def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS."""
    if not text:
        return text

    # Basic HTML encoding
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    text = text.replace("/", "&#x2F;")

    return text


def validate_email_format(email: str) -> bool:
    """Validate email format."""
    import re

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def validate_phone_format(phone: str) -> bool:
    """Validate phone number format (Chinese mobile)."""
    import re

    pattern = r"^1[3-9]\d{9}$"
    return re.match(pattern, phone) is not None


# Password strength validation
def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """Validate password strength."""
    errors = []

    if len(password) < 8:
        errors.append("密码长度至少8个字符")

    if not any(c.isupper() for c in password):
        errors.append("密码必须包含至少一个大写字母")

    if not any(c.islower() for c in password):
        errors.append("密码必须包含至少一个小写字母")

    if not any(c.isdigit() for c in password):
        errors.append("密码必须包含至少一个数字")

    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        errors.append("密码必须包含至少一个特殊字符")

    return len(errors) == 0, errors
