"""Canonical client identity through explicitly configured trusted proxy networks."""

from __future__ import annotations

import ipaddress
from collections.abc import Mapping, Sequence

from fastapi import Request

FALLBACK_IP = "127.0.0.1"


def _canonical(value: str) -> str:
    if not isinstance(value, str) or "%" in value:
        raise ValueError("Scoped addresses cannot establish client identity")
    address = ipaddress.ip_address(value.strip())
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return str(address)


def is_valid_ip(ip_str: str) -> bool:
    try:
        _canonical(ip_str)
        return True
    except (ValueError, AttributeError):
        return False


def extract_client_ip(
    headers: Mapping[str, str] | None = None,
    client_host: str | None = None,
    trust_proxy: bool = False,
    trusted_proxies: Sequence[str] = (),
) -> str:
    """Walk XFF right-to-left only from a verified trusted socket peer.

    Malformed chains fail back to the socket. Vendor identity headers have no
    authority here. Uvicorn must preserve the socket peer (--no-proxy-headers).
    """
    try:
        peer = _canonical(client_host or FALLBACK_IP)
    except ValueError:
        return FALLBACK_IP
    networks = [ipaddress.ip_network(cidr) for cidr in trusted_proxies]

    def trusted(value: str) -> bool:
        address = ipaddress.ip_address(value)
        return any(address in network for network in networks)

    if not trust_proxy or not trusted(peer):
        return peer
    values = [v for k, v in (headers or {}).items() if k.lower() == "x-forwarded-for"]
    if len(values) != 1:
        return peer
    forwarded = values[0]
    if not forwarded or len(forwarded) > 2048:
        return peer
    parts = forwarded.split(",")
    if len(parts) > 16:
        return peer
    try:
        chain = [_canonical(part) for part in parts]
    except ValueError:
        return peer
    for hop in reversed(chain):
        if not trusted(peer):
            break
        peer = hop
    return peer


def get_client_ip(request: Request) -> str:
    settings = getattr(request.scope.get("app", None), "state", None)
    settings = getattr(settings, "settings", None)
    return extract_client_ip(
        headers=request.headers,
        client_host=request.client.host if request.client else None,
        trust_proxy=getattr(settings, "TRUST_PROXY_HEADERS", False),
        trusted_proxies=getattr(settings, "TRUSTED_PROXY_CIDRS", ()),
    )
