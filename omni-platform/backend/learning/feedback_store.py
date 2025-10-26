import os
import sqlite3
import json
import time
from typing import Dict, Any, Optional, List, Tuple

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DATA_DIR, "learning.db")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS feedback_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,
  agent_type TEXT NOT NULL,
  provider TEXT,
  model TEXT,
  task_type TEXT,
  success INTEGER,
  reward REAL,
  latency_ms INTEGER,
  meta_json TEXT
);

CREATE TABLE IF NOT EXISTS policy_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  provider_priority TEXT, -- comma-separated list
  model_prefs_json TEXT   -- map task_type -> {provider: model}
);

CREATE TABLE IF NOT EXISTS memory_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  ts INTEGER NOT NULL,
  agent_type TEXT,
  event_json TEXT
);
"""

class FeedbackStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH
        self._ensure_db()

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)

    def insert_event(self, event: Dict[str, Any]) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO feedback_events (ts, agent_type, provider, model, task_type, success, reward, latency_ms, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(event.get("ts") or time.time()),
                    event.get("agent_type"),
                    event.get("provider"),
                    event.get("model"),
                    event.get("task_type"),
                    1 if event.get("success") else 0,
                    float(event.get("reward") or (1.0 if event.get("success") else 0.0)),
                    int(event.get("latency_ms") or 0),
                    json.dumps(event.get("meta") or {}),
                ),
            )
            conn.commit()
            return cur.lastrowid

    def summary_by_provider(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT provider,
                       COUNT(*) AS total,
                       SUM(success) AS success_count,
                       AVG(reward) AS avg_reward,
                       AVG(latency_ms) AS avg_latency
                FROM feedback_events
                WHERE provider IS NOT NULL
                GROUP BY provider
                ORDER BY avg_reward DESC
                """
            )
            rows = cur.fetchall()
        return [
            {
                "provider": r[0],
                "total": r[1],
                "success": r[2],
                "avg_reward": r[3],
                "avg_latency": r[4],
            }
            for r in rows
        ]

    def summary_by_agent(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT agent_type,
                       COUNT(*) AS total,
                       SUM(success) AS success_count,
                       AVG(reward) AS avg_reward,
                       AVG(latency_ms) AS avg_latency
                FROM feedback_events
                GROUP BY agent_type
                ORDER BY avg_reward DESC
                """
            )
            rows = cur.fetchall()
        return [
            {
                "agent_type": r[0],
                "total": r[1],
                "success": r[2],
                "avg_reward": r[3],
                "avg_latency": r[4],
            }
            for r in rows
        ]

    def get_policy_state(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT provider_priority, model_prefs_json FROM policy_state WHERE id=1")
            row = cur.fetchone()
            if not row:
                return {"provider_priority": None, "model_prefs": {}}
            return {
                "provider_priority": row[0],
                "model_prefs": json.loads(row[1] or "{}"),
            }

    def set_policy_state(self, provider_priority: Optional[str], model_prefs: Dict[str, Dict[str, str]]) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM policy_state WHERE id=1")
            exists = cur.fetchone()[0] > 0
            if exists:
                cur.execute(
                    "UPDATE policy_state SET provider_priority=?, model_prefs_json=? WHERE id=1",
                    (provider_priority, json.dumps(model_prefs)),
                )
            else:
                cur.execute(
                    "INSERT INTO policy_state (id, provider_priority, model_prefs_json) VALUES (1, ?, ?)",
                    (provider_priority, json.dumps(model_prefs)),
                )
            conn.commit()

    def recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ts, agent_type, provider, model, task_type, success, reward, latency_ms, meta_json FROM feedback_events ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        return [
            {
                "ts": r[0],
                "agent_type": r[1],
                "provider": r[2],
                "model": r[3],
                "task_type": r[4],
                "success": bool(r[5]),
                "reward": r[6],
                "latency_ms": r[7],
                "meta": json.loads(r[8] or "{}"),
            }
            for r in rows
        ]

class MemoryStore:
    def __init__(self, db_path: Optional[str] = None) -> None:
        self.db_path = db_path or DB_PATH
        self._ensure_db()

    def _ensure_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(SCHEMA_SQL)

    def append(self, session_id: str, event: Dict[str, Any], agent_type: Optional[str] = None) -> int:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO memory_events (session_id, ts, agent_type, event_json) VALUES (?, ?, ?, ?)",
                (session_id, int(time.time()), agent_type, json.dumps(event)),
            )
            conn.commit()
            return cur.lastrowid

    def history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT ts, agent_type, event_json FROM memory_events WHERE session_id=? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            )
            rows = cur.fetchall()
        return [
            {
                "ts": r[0],
                "agent_type": r[1],
                "event": json.loads(r[2] or "{}"),
            }
            for r in rows
        ]