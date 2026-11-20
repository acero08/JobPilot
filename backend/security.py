"""Request checks that keep the local API reachable only from the local UI."""
from fastapi.responses import JSONResponse

import config

TOKEN_HEADER = "X-JobPilot-Token"


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
    # CORS only hides responses; it does not stop a cross-site form POST from
    # running. Browsers always send Origin on such requests, so reject them here.
    origin = request.headers.get("origin")
    if request.url.path.startswith("/api") and origin and origin not in config.TRUSTED_ORIGINS:
        return JSONResponse({"detail": "Origin not allowed"}, status_code=403)
    return await call_next(request)
