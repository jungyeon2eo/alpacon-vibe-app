import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    """Open a short-lived autocommit connection."""
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_db():
    """Create the checks table if it does not exist. Safe to call repeatedly."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checks (
                id          SERIAL PRIMARY KEY,
                url         TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'queued',
                http_status INTEGER,
                latency_ms  INTEGER,
                checked_at  TIMESTAMPTZ,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
