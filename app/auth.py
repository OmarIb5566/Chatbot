import hashlib
import hmac
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings

_DB_PATH = Path(settings.app_db_path)
_PBKDF2_ITERATIONS = 260_000


@contextmanager
def _connect():
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
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
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
    _bootstrap_admin()


def _hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS).hex()


def create_user(username: str, password: str) -> None:
    salt = os.urandom(16)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO users (username, salt, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, salt.hex(), _hash_password(password, salt), datetime.now(timezone.utc).isoformat()),
        )


def user_exists(username: str) -> bool:
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone()
        return row is not None


def verify_user(username: str, password: str) -> bool:
    with _connect() as conn:
        row = conn.execute(
            "SELECT salt, password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row is None:
        return False
    salt = bytes.fromhex(row["salt"])
    return hmac.compare_digest(_hash_password(password, salt), row["password_hash"])


def list_users() -> list[str]:
    with _connect() as conn:
        rows = conn.execute("SELECT username FROM users ORDER BY username").fetchall()
        return [r["username"] for r in rows]


def delete_user(username: str) -> bool:
    with _connect() as conn:
        cur = conn.execute("DELETE FROM users WHERE username = ?", (username,))
        return cur.rowcount > 0


def _bootstrap_admin() -> None:
    """Create one account from env vars on first run so initial setup isn't a chicken-and-egg problem."""
    if list_users():
        return
    if settings.bootstrap_admin_username and settings.bootstrap_admin_password:
        create_user(settings.bootstrap_admin_username, settings.bootstrap_admin_password)
