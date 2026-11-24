from typing import Optional
from urllib.parse import urlsplit

DEFAULT_PORTS = {"http": 80, "https": 443}


def canonical_address(url: str) -> Optional[str]:
    try:
        parts = urlsplit(url.strip())
        port = parts.port
    except ValueError:
        return None
    scheme = parts.scheme.lower()
    host = parts.hostname
    if scheme not in DEFAULT_PORTS or not host:
        return None
    port = port or DEFAULT_PORTS[scheme]
    if ":" in host:
        host = f"[{host}]"
    path = parts.path.rstrip("/")
    return f"{scheme}://{host.lower()}:{port}{path}"
