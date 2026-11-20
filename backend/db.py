"""SQLite storage for profiles.

Profiles are stored as JSON documents in a single table, because their shape
is owned by the UI and changes more often than a relational schema would.
"""
import json
import sqlite3

from config import DATA_DIR

RESUME_DIR = DATA_DIR / "resumes"
DATA_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "jobpilot.db"


def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL
            )"""
        )


def _row(r):
    d = json.loads(r["data"])
    d["id"] = r["id"]
    return d


def list_profiles():
    with conn() as c:
        return [_row(r) for r in c.execute("SELECT * FROM profiles ORDER BY id")]


def get_profile(pid):
    with conn() as c:
        r = c.execute("SELECT * FROM profiles WHERE id=?", (pid,)).fetchone()
        return _row(r) if r else None


def create_profile(data):
    with conn() as c:
        cur = c.execute("INSERT INTO profiles (data) VALUES (?)", (json.dumps(data),))
        return cur.lastrowid


def update_profile(pid, data):
    data = {k: v for k, v in data.items() if k != "id"}
    with conn() as c:
        c.execute("UPDATE profiles SET data=? WHERE id=?", (json.dumps(data), pid))


def delete_profile(pid):
    with conn() as c:
        c.execute("DELETE FROM profiles WHERE id=?", (pid,))
