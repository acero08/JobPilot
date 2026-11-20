"""App settings, loaded from backend/.env (see .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
# Host header values accepted by the API. Anything else is treated as a DNS
# rebinding attempt, where a remote site resolves its own name to 127.0.0.1.
ALLOWED_HOST_HEADERS = {"127.0.0.1", "localhost"}

HOST = os.getenv("JOBPILOT_HOST", "127.0.0.1")
ALLOW_NON_LOOPBACK = os.getenv("JOBPILOT_ALLOW_NON_LOOPBACK", "0") == "1"
PORT = int(os.getenv("JOBPILOT_PORT", "8000"))
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "JOBPILOT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
DATA_DIR = Path(os.getenv("JOBPILOT_DATA_DIR", "data")).expanduser()
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR  # relative paths are relative to backend/
HEADLESS = os.getenv("JOBPILOT_HEADLESS", "0") == "1"
PAGE_SETTLE_MS = int(os.getenv("JOBPILOT_PAGE_SETTLE_MS", "2500"))


def check_bind_host(host):
    """Refuse to listen beyond loopback unless explicitly allowed.

    The API exposes personal data, so binding to 0.0.0.0 or a LAN address
    must be a deliberate choice rather than a configuration typo.
    """
    if host not in LOOPBACK_HOSTS and not ALLOW_NON_LOOPBACK:
        raise SystemExit(
            f"Refusing to bind to {host!r}. JobPilot listens on loopback only; "
            "set JOBPILOT_ALLOW_NON_LOOPBACK=1 to override."
        )
