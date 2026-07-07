import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

_DB_PATH = Path(settings.app_db_path)


@contextmanager
def _connect():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL CHECK(role IN ('user','assistant')),
                content TEXT NOT NULL,
                sql TEXT,
                created_at TEXT NOT NULL
            )
            """
        )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_conversation(username: str, title: str) -> int:
    title = title.strip().replace("\n", " ")
    if len(title) > 80:
        title = title[:77] + "..."
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO conversations (username, title, created_at) VALUES (?, ?, ?)",
            (username, title, _now()),
        )
        return cur.lastrowid


def add_message(conversation_id: int, role: str, content: str, sql: str | None = None) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, sql, created_at) VALUES (?, ?, ?, ?, ?)",
            (conversation_id, role, content, sql, _now()),
        )


def conversation_exists(conversation_id: int, username: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND username = ?", (conversation_id, username)
        ).fetchone()
        return row is not None


def list_conversations(username: str) -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.title, c.created_at,
                   (SELECT content FROM messages m WHERE m.conversation_id = c.id
                    ORDER BY m.id DESC LIMIT 1) AS last_message
            FROM conversations c
            WHERE c.username = ?
            ORDER BY c.id DESC
            """,
            (username,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_conversation(conversation_id: int, username: str) -> dict | None:
    with _connect() as conn:
        conv = conn.execute(
            "SELECT id, title, created_at FROM conversations WHERE id = ? AND username = ?",
            (conversation_id, username),
        ).fetchone()
        if conv is None:
            return None
        messages = conn.execute(
            "SELECT role, content, sql, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,),
        ).fetchall()
        return {
            "id": conv["id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "messages": [dict(m) for m in messages],
        }


def delete_conversation(conversation_id: int, username: str) -> bool:
    with _connect() as conn:
        cur = conn.execute(
            "DELETE FROM conversations WHERE id = ? AND username = ?", (conversation_id, username)
        )
        return cur.rowcount > 0
