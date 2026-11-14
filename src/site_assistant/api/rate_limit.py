"""Small in-memory rate limiter for the temporary public demo."""

from collections import deque
from ipaddress import ip_address
from math import ceil
from threading import Lock
from time import monotonic

from starlette.requests import Request


class SlidingWindowRateLimiter:
    """Limit requests per client over a rolling time window."""

    def __init__(
        self,
        max_requests: int,
        window_seconds: float = 60.0,
        max_clients: int = 4096,
    ) -> None:
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.max_clients = max_clients
        self._requests: dict[str, deque[float]] = {}
        self._lock = Lock()

    def allow(self, client_key: str, now: float | None = None) -> tuple[bool, int]:
        """Return whether a request is allowed and the retry delay in seconds."""
        current_time = monotonic() if now is None else now
        cutoff = current_time - self.window_seconds

        with self._lock:
            if client_key not in self._requests:
                self._remove_expired_clients(cutoff)
                if len(self._requests) >= self.max_clients:
                    oldest_key = min(
                        self._requests,
                        key=lambda key: self._requests[key][0],
                    )
                    self._requests.pop(oldest_key, None)
                self._requests[client_key] = deque()

            events = self._requests[client_key]
            while events and events[0] <= cutoff:
                events.popleft()

            if len(events) >= self.max_requests:
                retry_after = max(
                    1,
                    ceil(self.window_seconds - (current_time - events[0])),
                )
                return False, retry_after

            events.append(current_time)
            return True, 0

    def _remove_expired_clients(self, cutoff: float) -> None:
        """Drop inactive client buckets to keep memory use bounded."""
        expired = [
            key
            for key, events in self._requests.items()
            if not events or events[-1] <= cutoff
        ]
        for key in expired:
            self._requests.pop(key, None)


def client_identifier(request: Request) -> str:
    """Use Cloudflare's visitor IP only when the local tunnel is the peer."""
    peer = request.client.host if request.client else "unknown"

    try:
        peer_address = ip_address(peer)
    except ValueError:
        return peer

    if peer_address.is_loopback:
        forwarded_address = request.headers.get("cf-connecting-ip", "").strip()
        if forwarded_address:
            try:
                return str(ip_address(forwarded_address))
            except ValueError:
                pass

    return str(peer_address)
