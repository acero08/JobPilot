"""App settings, loaded from backend/.env (see .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

HOST = os.getenv("JOBPILOT_HOST", "127.0.0.1")
PORT = int(os.getenv("JOBPILOT_PORT", "8000"))
CORS_ORIGINS = [o.strip() for o in os.getenv(
    "JOBPILOT_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]
DATA_DIR = Path(os.getenv("JOBPILOT_DATA_DIR", "data")).expanduser()
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR  # relative paths are relative to backend/
HEADLESS = os.getenv("JOBPILOT_HEADLESS", "0") == "1"
PAGE_SETTLE_MS = int(os.getenv("JOBPILOT_PAGE_SETTLE_MS", "2500"))
