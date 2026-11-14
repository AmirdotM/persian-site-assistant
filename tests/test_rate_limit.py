"""Unit tests for public-demo request limiting."""

from starlette.requests import Request

from site_assistant.api.rate_limit import SlidingWindowRateLimiter, client_identifier


def test_sliding_window_limits_requests_and_recovers_after_expiry() -> None:
    limiter = SlidingWindowRateLimiter(max_requests=2, window_seconds=10)

    assert limiter.allow("visitor-a", now=100.0) == (True, 0)
    assert limiter.allow("visitor-a", now=101.0) == (True, 0)
    allowed, retry_after = limiter.allow("visitor-a", now=102.0)

    assert not allowed
    assert retry_after == 8
    assert limiter.allow("visitor-a", now=110.0) == (True, 0)


def test_cloudflare_visitor_ip_is_used_only_for_loopback_tunnel_peer() -> None:
    local_scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [(b"cf-connecting-ip", b"203.0.113.8")],
        "client": ("127.0.0.1", 54321),
        "server": ("127.0.0.1", 8765),
    }
    remote_scope = {
        **local_scope,
        "client": ("198.51.100.9", 54321),
    }

    assert client_identifier(Request(local_scope)) == "203.0.113.8"
    assert client_identifier(Request(remote_scope)) == "198.51.100.9"
