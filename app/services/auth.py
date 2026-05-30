"""API key authentication and rate-limit dependency for FastAPI routes."""

from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status

from app.config import settings
from app.services.rate_limiter import allow_request


def get_api_key(x_api_key: str | None = Header(None)) -> str:
    expected = getattr(settings, "API_KEY", None)
    # If no API key configured, operate in permissive dev mode: accept requests
    # and apply rate limits under an anonymous key.
    if expected is None:
        key = x_api_key or "__anonymous__"
        allowed = allow_request(key)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )
        return key

    # If API key is configured, require it matches X-API-KEY header
    if x_api_key is None or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    # rate limit check per API key
    allowed = allow_request(x_api_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )
    return x_api_key


def require_api_key(api_key: str = Depends(get_api_key)) -> str:
    return api_key
