"""
Simple in-memory sliding-window rate limiter.

In-memory is appropriate for this prototype (single process, coursework
scale) -- a production deployment with multiple server instances would
need a shared store like Redis instead, since each process would
otherwise track limits independently.
"""

import time
from collections import defaultdict, deque

DEFAULT_MAX_REQUESTS = 20
DEFAULT_WINDOW_SECONDS = 60


class RateLimiter:
    def __init__(self, max_requests: int = DEFAULT_MAX_REQUESTS, window_seconds: int = DEFAULT_WINDOW_SECONDS):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Maps a client identifier (e.g. IP address) to a deque of
        # timestamps of their recent requests.
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, client_id: str) -> bool:
        """
        Returns True if the request is allowed, False if the client has
        exceeded the limit. Also records this request if allowed.
        """
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._requests[client_id]

        # Drop timestamps that have aged out of the current window.
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        if len(timestamps) >= self.max_requests:
            return False

        timestamps.append(now)
        return True


# Single shared instance for the whole application.
rate_limiter = RateLimiter()