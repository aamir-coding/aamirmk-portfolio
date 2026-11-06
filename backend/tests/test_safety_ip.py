"""Tests for client IP extraction and reverse proxy header handling."""

from starlette.datastructures import Headers
from starlette.requests import Request

from app.main import create_app
from app.safety.ip import extract_client_ip, get_client_ip, is_valid_ip
from app.settings import Settings


def test_is_valid_ip():
    """Verify validation of IPv4, IPv6, and invalid strings."""
    assert is_valid_ip("192.168.1.1") is True
    assert is_valid_ip("127.0.0.1") is True
    assert is_valid_ip("203.0.113.195") is True
    assert is_valid_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334") is True
    assert is_valid_ip("::1") is True

    assert is_valid_ip("") is False
    assert is_valid_ip("not-an-ip") is False
    assert is_valid_ip("999.999.999.999") is False
    assert is_valid_ip("192.168.1.1/24") is False
    assert is_valid_ip(None) is False  # type: ignore[arg-type]


def test_extract_client_ip_direct_socket():
    """Verify direct socket host fallback when no proxy headers are present."""
    ip = extract_client_ip(headers={}, client_host="198.51.100.42")
    assert ip == "198.51.100.42"


def test_extract_client_ip_fallback_default():
    """Verify fallback to 127.0.0.1 when host and headers are missing or invalid."""
    assert extract_client_ip(headers={}, client_host=None) == "127.0.0.1"
    assert extract_client_ip(headers={}, client_host="invalid-host") == "127.0.0.1"


def test_extract_client_ip_cf_connecting_ip():
    """Unverified vendor headers have no authority over the socket peer."""
    headers = {
        "cf-connecting-ip": "198.51.100.10",
        "true-client-ip": "198.51.100.20",
        "x-forwarded-for": "198.51.100.30, 10.0.0.1",
    }
    ip = extract_client_ip(headers=headers, client_host="10.0.0.2")
    assert ip == "10.0.0.2"


def test_extract_client_ip_true_client_ip():
    """True-Client-IP alone cannot establish a trusted identity."""
    headers = {
        "true-client-ip": "198.51.100.20",
        "x-forwarded-for": "198.51.100.30, 10.0.0.1",
    }
    ip = extract_client_ip(headers=headers, client_host="10.0.0.2")
    assert ip == "10.0.0.2"


def test_extract_client_ip_x_forwarded_for_chain():
    """A verified chain walks trusted hops from the socket toward the client."""
    headers = {
        "x-forwarded-for": "203.0.113.55, 10.100.0.1, 10.200.0.1",
    }
    ip = extract_client_ip(
        headers=headers,
        client_host="10.200.0.2",
        trust_proxy=True,
        trusted_proxies=["10.0.0.0/8"],
    )
    assert ip == "203.0.113.55"


def test_extract_client_ip_x_forwarded_for_with_malformed_entries():
    """Malformed chains fall back to the socket rather than skipping entries."""
    headers = {
        "x-forwarded-for": "unknown, bad_ip, 203.0.113.77, 10.0.0.1",
    }
    ip = extract_client_ip(headers=headers, client_host="10.0.0.2")
    assert ip == "10.0.0.2"


def test_extract_client_ip_untrusted_proxies():
    """Verify trust_proxy=False ignores proxy headers and uses direct client_host."""
    headers = {
        "x-forwarded-for": "203.0.113.55",
        "cf-connecting-ip": "203.0.113.66",
    }
    ip = extract_client_ip(
        headers=headers, client_host="192.168.1.100", trust_proxy=False
    )
    assert ip == "192.168.1.100"


def test_get_client_ip_dependency(test_settings: Settings):
    """Verify get_client_ip works as a FastAPI dependency inside request scope."""
    app = create_app(
        settings=test_settings.model_copy(
            update={
                "TRUST_PROXY_HEADERS": True,
                "TRUSTED_PROXY_CIDRS": ["10.0.0.0/24"],
            }
        )
    )
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/health",
        "headers": Headers({"x-forwarded-for": "198.51.100.88"}).raw,
        "client": ("10.0.0.5", 12345),
        "app": app,
    }
    request = Request(scope)
    resolved_ip = get_client_ip(request)
    assert resolved_ip == "198.51.100.88"
