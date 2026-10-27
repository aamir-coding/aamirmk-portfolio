"""Client IP extraction with proxy awareness and spoofing defense."""

from __future__ import annotations

import ipaddress
import logging
from collections.abc import Mapping
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)

FALLBACK_IP = "127.0.0.1"


def is_valid_ip(ip_str: str) -> bool:
    """Validate whether an input string is a valid IPv4 or IPv6 address."""
    if not ip_str or not isinstance(ip_str, str):
        return False
    try:
        ipaddress.ip_address(ip_str.strip())
        return True
    except ValueError:
        return False


def extract_client_ip(
    headers: Mapping[str, str] | None = None,
    client_host: str | None = None,
    trust_proxy: bool = True,
) -> str:
    """Extract real client IP address from request headers or socket host.

    Order of precedence when trust_proxy is True:
    1. CF-Connecting-IP (Cloudflare)
    2. True-Client-IP (Akamai/Cloudflare enterprise)
    3. X-Forwarded-For (standard reverse proxy chain)
       - Parsed into list of trimmed tokens
       - Validated against ipaddress
       - Returns the leftmost valid non-spoofed IP in the chain
    4. Direct socket client host (request.client.host)
    5. Fallback IP (127.0.0.1)
    """
    headers = headers or {}
    lower_headers = {k.lower(): v for k, v in headers.items()}

    if trust_proxy:
        # 1. Cloudflare connecting IP
        cf_ip = lower_headers.get("cf-connecting-ip")
        if cf_ip and is_valid_ip(cf_ip.strip()):
            return cf_ip.strip()

        # 2. True-Client-IP
        true_ip = lower_headers.get("true-client-ip")
        if true_ip and is_valid_ip(true_ip.strip()):
            return true_ip.strip()

        # 3. X-Forwarded-For chain
        forwarded_for = lower_headers.get("x-forwarded-for")
        if forwarded_for:
            # Comma-separated list: "client, proxy1, proxy2"
            raw_ips = [
                part.strip() for part in forwarded_for.split(",") if part.strip()
            ]
            valid_ips = [ip for ip in raw_ips if is_valid_ip(ip)]
            if valid_ips:
                # Return leftmost valid client IP
                return valid_ips[0]

    # 4. Direct socket host fallback
    if client_host and is_valid_ip(client_host.strip()):
        return client_host.strip()

    return FALLBACK_IP


def get_client_ip(request: Request) -> str:
    """FastAPI dependency or helper to retrieve the client IP from Request."""
    client_host = request.client.host if request.client else None
    settings: Any = getattr(request.app.state, "settings", None)
    trust_proxy = getattr(settings, "TRUST_PROXY_HEADERS", True) if settings else True
    return extract_client_ip(
        headers=request.headers,
        client_host=client_host,
        trust_proxy=trust_proxy,
    )
