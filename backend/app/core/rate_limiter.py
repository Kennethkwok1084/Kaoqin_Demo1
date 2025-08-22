"""
Rate limiting utilities and middleware for the application.
Provides decorators and middleware for API endpoint rate limiting.
"""

import functools
import logging
from typing import Callable, Optional

from fastapi import HTTPException, Request, status

from app.core.security import rate_limiter as global_rate_limiter

logger = logging.getLogger(__name__)


def rate_limit(
    max_requests: int = 5,
    window_seconds: int = 60,
    key_func: Optional[Callable[[Request], str]] = None,
    error_message: str = "Too many requests. Please try again later.",
) -> Callable:
    """
    Rate limiting decorator for FastAPI endpoints.

    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        key_func: Function to generate rate limit key from request
        error_message: Error message for rate limit exceeded

    Returns:
        Decorator function
    """

    def default_key_func(request: Request) -> str:
        """Default key function using client IP"""
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:{client_ip}"

    actual_key_func = key_func or default_key_func

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request from arguments
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # If no request found, look in kwargs
                request = kwargs.get("request")

            if request:
                # Generate rate limit key
                key = actual_key_func(request)

                # Check rate limit
                if not global_rate_limiter.is_allowed(
                    key, max_requests, window_seconds
                ):
                    logger.warning(f"Rate limit exceeded for key: {key}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=error_message,
                    )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


def login_rate_limit(
    max_requests: int = 5,
    window_seconds: int = 60,
) -> Callable:
    """
    Specialized rate limiting decorator for login endpoints.
    Uses client IP for rate limiting key.
    """

    def key_func(request: Request) -> str:
        client_ip = request.client.host if request.client else "unknown"
        return f"login:{client_ip}"

    return rate_limit(
        max_requests=max_requests,
        window_seconds=window_seconds,
        key_func=key_func,
        error_message="Too many login attempts. Please try again later.",
    )
