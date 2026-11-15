"""SQLite persistence for complete runs, node events, and all output fields."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "data" / "news_runs.db"


def _db_path() -> Path:
    return Path(os.getenv("NEWS_DB_PATH", str(DEFAULT_DB_PATH)))


def _connect() -> sqlite3.Connection:
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path), timeout=10)
    con.row_factory = sqlite3.Row
    con.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            input_type TEXT NOT NULL,
            source_url TEXT,
            status TEXT NOT NULL,
            word_count INTEGER,
            category TEXT,
            summary TEXT,
            state_json TEXT NOT NULL
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_runs_time ON runs(created_at DESC)")
    return con


def save_run(state: dict[str, Any]) -> None:
    """Store complete state; never include credentials in the state."""
    payload = json.dumps(state, ensure_ascii=False, default=str)
    con = _connect()
    try:
        with con:
            con.execute(
                """INSERT OR REPLACE INTO runs
                    (run_id, created_at, input_type, source_url, status, word_count,
                    category, summary, state_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    state.get("run_id"), state.get("created_at"),
                    state.get("input_type"), state.get("source_url"),
                    state.get("status", "unknown"), state.get("word_count", 0),
                    state.get("category"), state.get("summary"), payload,
                ),
            )
    finally:
        con.close()


def list_runs(limit: int = 50) -> list[dict[str, Any]]:
    con = _connect()
    try:
        rows = con.execute(
            """SELECT run_id, created_at, input_type, source_url, status,
                      word_count, category, summary
               FROM runs ORDER BY created_at DESC, rowid DESC LIMIT ?""",
            (min(max(limit, 1), 500),),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        con.close()


def get_run(run_id: str) -> dict[str, Any] | None:
    con = _connect()
    try:
        row = con.execute(
            "SELECT state_json FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        return json.loads(row["state_json"]) if row else None
    finally:
        con.close()


def get_run_stats() -> dict[str, int]:
    """Accurate totals for the dashboard, not limited by history pagination."""
    con = _connect()
    try:
        rows = con.execute(
            "SELECT status, COUNT(*) AS amount FROM runs GROUP BY status"
        ).fetchall()
        totals = {str(row["status"]): int(row["amount"]) for row in rows}
        return {"total": sum(totals.values()), **totals}
    finally:
        con.close()
