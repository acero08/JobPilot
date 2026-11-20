"""Request checks that keep the local API reachable only from the local UI."""
import os
import secrets

from fastapi.responses import JSONResponse

import config

TOKEN_HEADER = "X-JobPilot-Token"
TOKEN_FILE = config.DATA_DIR / "api-token"


def load_or_create_token(path=TOKEN_FILE):
    """Return the per-install API token, creating it on first run.

    The file is created with mode 600 so other local users cannot read it.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path.read_text().strip()
    token = secrets.token_urlsafe(32)
    with os.fdopen(fd, "w") as f:
        f.write(token)
    return token


API_TOKEN = load_or_create_token()


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
    if request.url.path.startswith("/api"):
        sent = request.headers.get(TOKEN_HEADER, "")
        if not secrets.compare_digest(sent.encode(), API_TOKEN.encode()):
            return JSONResponse({"detail": "Missing or invalid API token"}, status_code=401)
    return await call_next(request)
