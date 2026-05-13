import time


class FixedWindowRateLimiter:
    """Rate limiter in-memory por chave (phone). Fixed window."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60) -> None:
        self._max = max_requests
        self._window = window_seconds
        self._state: dict[str, tuple[int, float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        count, window_start = self._state.get(key, (0, now))
        if now - window_start > self._window:
            self._state[key] = (1, now)
            return True
        if count >= self._max:
            return False
        self._state[key] = (count + 1, window_start)
        return True
