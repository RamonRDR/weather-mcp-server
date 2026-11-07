"""Small, bounded per-process limiter for a local single-host stdio server."""

import asyncio
from time import monotonic

from weather_mcp_server.errors import TooManyRequests


class RateLimiter:
    def __init__(self, calls: int, window_seconds: int) -> None:
        self.calls = calls
        self.window_seconds = window_seconds
        self._lock = asyncio.Lock()
        self._start = monotonic()
        self._count = 0

    async def check(self) -> None:
        async with self._lock:
            now = monotonic()
            if now - self._start >= self.window_seconds:
                self._start = now
                self._count = 0
            if self._count >= self.calls:
                raise TooManyRequests
            self._count += 1
