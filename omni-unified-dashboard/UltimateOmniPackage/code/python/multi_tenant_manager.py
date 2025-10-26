from pathlib import Path
import sqlite3
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
TENANTS_DIR = ROOT / "UltimateOmniPackage" / "code" / "databases" / "tenants"
TENANTS_DIR.mkdir(parents=True, exist_ok=True)

def tenant_db_path(tenant_id: str) -> Path:
    safe = tenant_id.replace("/", "_").replace("\\", "_")
    return TENANTS_DIR / f"tenant_{safe}.sqlite3"

def init_tenant(tenant_id: str) -> Path:
    path = tenant_db_path(tenant_id)
    first_time = not path.exists()
    conn = sqlite3.connect(path)
    if first_time:
        conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              email TEXT UNIQUE,
              name TEXT,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS events (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              type TEXT,
              payload TEXT,
              created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
    conn.close()
    return path

def with_conn(tenant_id: str):
    path = init_tenant(tenant_id)
    return sqlite3.connect(path)

def add_event(tenant_id: str, event_type: str, payload: str):
    with with_conn(tenant_id) as conn:
        conn.execute("INSERT INTO events(type, payload) VALUES (?, ?)", (event_type, payload))
        conn.commit()

def get_events(tenant_id: str, limit: int = 100):
    with with_conn(tenant_id) as conn:
        cur = conn.execute("SELECT id, type, payload, created_at FROM events ORDER BY id DESC LIMIT ?", (limit,))
        return cur.fetchall()