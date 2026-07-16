import logging
import os

import psycopg2
import psycopg2.extras
from psycopg2.pool import ThreadedConnectionPool

from app.config import settings

logger = logging.getLogger(__name__)

_pool: ThreadedConnectionPool | None = None


def get_pool() -> ThreadedConnectionPool:
    global _pool
    if _pool is None:
        options = (
            f"-c statement_timeout={settings.db_statement_timeout_ms} "
            f"-c default_transaction_read_only=on"
        )
        database_url = os.environ.get("DATABASE_URL")
        if database_url:
            # Use Replit's managed DATABASE_URL (preferred)
            _pool = ThreadedConnectionPool(
                settings.db_pool_min,
                settings.db_pool_max,
                database_url,
                options=options,
            )
        else:
            _pool = ThreadedConnectionPool(
                settings.db_pool_min,
                settings.db_pool_max,
                host=settings.db_host,
                port=settings.db_port,
                dbname=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                options=options,
            )
    return _pool


class QueryError(Exception):
    """A SQL statement failed to execute against Postgres."""


def run_select(sql: str, max_rows: int) -> tuple[list[str], list[dict]]:
    """Execute a single read-only SELECT and return (columns, rows).

    Any failure raises QueryError with the original Postgres error message,
    which the caller can feed back to the LLM for a repair attempt.
    """
    pool = get_pool()
    conn = pool.getconn()
    try:
        conn.rollback()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql)
            if cur.description is None:
                return [], []
            columns = [d.name for d in cur.description]
            rows = cur.fetchmany(max_rows)
            return columns, [dict(r) for r in rows]
    except psycopg2.Error as exc:
        conn.rollback()
        raise QueryError(str(exc).strip()) from exc
    finally:
        pool.putconn(conn)


def health_check() -> bool:
    try:
        run_select("SELECT 1", max_rows=1)
        return True
    except QueryError:
        return False
