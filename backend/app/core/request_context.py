"""Request context helpers for per-request tracing metadata."""

from contextvars import ContextVar, Token
from typing import Optional


_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def set_request_id(request_id: str) -> Token[Optional[str]]:
    """Store request_id for current async context."""
    return _request_id_ctx.set(request_id)


def reset_request_id(token: Token[Optional[str]]) -> None:
    """Reset request_id context to previous value."""
    _request_id_ctx.reset(token)


def get_request_id(default: str = "") -> str:
    """Get request_id from current async context."""
    request_id = _request_id_ctx.get()
    if request_id:
        return request_id
    return default
