import os
import sys
import tempfile
from pathlib import Path

# Settings are read at import time, so point the data directory at a scratch
# location before any app module is imported.
os.environ["JOBPILOT_DATA_DIR"] = tempfile.mkdtemp(prefix="jobpilot-test-")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient

import main
import security


@pytest.fixture
def client():
    c = TestClient(main.app, base_url="http://localhost")
    c.headers[security.TOKEN_HEADER] = security.API_TOKEN
    return c


@pytest.fixture
def anon():
    return TestClient(main.app, base_url="http://localhost")
