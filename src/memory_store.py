from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VALID_STATUSES = {"open", "done", "archived"}


@dataclass(frozen=True)
class MemoryEntry:
    id: int
    created_at: str
    raw_transcript: str
    cleaned_text: str
    entry_type: str
    status: str
    due_at: str | None
    tags: list[str]
    metadata_json: dict[str, Any]


@dataclass(frozen=True)
class NewMemoryEntry:
    raw_transcript: str
    cleaned_text: str
    entry_type: str
    status: str = "open"
    due_at: str | None = None
    tags: list[str] | None = None
    metadata_json: dict[str, Any] | None = None


class MemoryStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        if self.db_path.parent and str(self.db_path.parent) != ".":
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    raw_transcript TEXT NOT NULL,
                    cleaned_text TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    due_at TEXT,
                    tags TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_created_at ON entries(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entries_type_status ON entries(entry_type, status)")

    def add_entry(self, entry: NewMemoryEntry) -> MemoryEntry:
        if entry.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status: {entry.status}")
        created_at = datetime.now(timezone.utc).isoformat()
        tags = entry.tags or []
        metadata = entry.metadata_json or {}
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO entries (
                    created_at, raw_transcript, cleaned_text, entry_type,
                    status, due_at, tags, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    created_at,
                    entry.raw_transcript,
                    entry.cleaned_text,
                    entry.entry_type,
                    entry.status,
                    entry.due_at,
                    json.dumps(tags),
                    json.dumps(metadata),
                ),
            )
            row_id = int(cursor.lastrowid)
        stored = self.get_entry(row_id)
        if stored is None:
            raise RuntimeError("Entry insert succeeded but could not be reloaded")
        return stored

    def get_entry(self, entry_id: int) -> MemoryEntry | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return _row_to_entry(row) if row else None

    def recent_entries(
        self,
        *,
        limit: int = 10,
        entry_types: Iterable[str] | None = None,
        statuses: Iterable[str] | None = None,
    ) -> list[MemoryEntry]:
        clauses: list[str] = []
        params: list[str | int] = []
        if entry_types:
            values = list(entry_types)
            clauses.append(f"entry_type IN ({','.join('?' for _ in values)})")
            params.extend(values)
        if statuses:
            values = list(statuses)
            clauses.append(f"status IN ({','.join('?' for _ in values)})")
            params.extend(values)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM entries {where} ORDER BY datetime(created_at) DESC, id DESC LIMIT ?",
                params,
            ).fetchall()
        return [_row_to_entry(row) for row in rows]

    def search_entries(
        self,
        keyword: str,
        *,
        limit: int = 10,
        statuses: Iterable[str] | None = None,
    ) -> list[MemoryEntry]:
        keyword = keyword.strip().lower()
        if not keyword:
            return []
        clauses = ["lower(cleaned_text) LIKE ?"]
        params: list[str | int] = [f"%{keyword}%"]
        if statuses:
            values = list(statuses)
            clauses.append(f"status IN ({','.join('?' for _ in values)})")
            params.extend(values)
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM entries
                WHERE {' AND '.join(clauses)}
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_row_to_entry(row) for row in rows]

    def mark_last_task_done(self) -> MemoryEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM entries
                WHERE entry_type = 'TASK' AND status = 'open'
                ORDER BY datetime(created_at) DESC, id DESC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            conn.execute("UPDATE entries SET status = 'done' WHERE id = ?", (row["id"],))
            updated = conn.execute("SELECT * FROM entries WHERE id = ?", (row["id"],)).fetchone()
        return _row_to_entry(updated) if updated else None


def _row_to_entry(row: sqlite3.Row) -> MemoryEntry:
    return MemoryEntry(
        id=int(row["id"]),
        created_at=str(row["created_at"]),
        raw_transcript=str(row["raw_transcript"]),
        cleaned_text=str(row["cleaned_text"]),
        entry_type=str(row["entry_type"]),
        status=str(row["status"]),
        due_at=row["due_at"],
        tags=json.loads(row["tags"] or "[]"),
        metadata_json=json.loads(row["metadata_json"] or "{}"),
    )

