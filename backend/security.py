"""Request checks that keep the local API reachable only from the local UI."""
from fastapi.responses import JSONResponse

import config


def host_allowed(host_header):
    host = (host_header or "").strip().lower()
    if host.startswith("["):  # bracketed IPv6 literal, e.g. [::1]:8000
        host = host[1:].split("]", 1)[0]
    else:
        host = host.rsplit(":", 1)[0]
    return host in config.ALLOWED_HOST_HEADERS


async def guard(request, call_next):
    if not host_allowed(request.headers.get("host")):
        return JSONResponse({"detail": "Invalid Host header"}, status_code=400)
    return await call_next(request)
