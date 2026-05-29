"""Rate limiter with optional Redis backend.

If `REDIS_URL` is set in settings and the `redis` package is available, the
module uses Redis INCR+EXPIRE for atomic counters across processes. Otherwise
it falls back to a simple in-memory windowed counter (suitable for dev).
"""

from __future__ import annotations

import time
from importlib import import_module
from threading import Lock
from typing import Dict

from app.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._store: Dict[str, tuple[int, float]] = {}
        self._lock = Lock()
        self._limit = int(getattr(settings, "RATE_LIMIT", 10))
        self._window = int(getattr(settings, "RATE_WINDOW", 60))

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            count, start = self._store.get(key, (0, now))
            if now - start >= self._window:
                # reset window
                self._store[key] = (1, now)
                return True
            if count < self._limit:
                self._store[key] = (count + 1, start)
                return True
            return False


class RedisRateLimiter:
    def __init__(self, url: str) -> None:
        redis_mod = import_module("redis")
        # Use Redis client; `from_url` convenience if available
        if hasattr(redis_mod, "from_url"):
            self._client = redis_mod.from_url(url)
        else:
            self._client = redis_mod.StrictRedis.from_url(url)
        self._limit = int(getattr(settings, "RATE_LIMIT", 10))
        self._window = int(getattr(settings, "RATE_WINDOW", 60))

    def allow(self, key: str) -> bool:
        k = f"rl:{key}"
        try:
            val = self._client.incr(k)
            if val == 1:
                # set expiry for window seconds
                self._client.expire(k, int(self._window))
            return val <= self._limit
        except Exception:
            # If Redis fails, be conservative and allow request
            return True


# Choose backend: Redis if configured, otherwise in-memory
_limiter = None
_redis_url = getattr(settings, "REDIS_URL", None)
if _redis_url:
    try:
        _limiter = RedisRateLimiter(_redis_url)
    except Exception:
        _limiter = InMemoryRateLimiter()
else:
    _limiter = InMemoryRateLimiter()


def allow_request(api_key: str) -> bool:
    return _limiter.allow(api_key)
