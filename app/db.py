import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    """Open a short-lived autocommit connection."""
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_db():
    """Create the game tables if missing, and ensure a single game row. Idempotent."""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS game (
                id          INTEGER PRIMARY KEY DEFAULT 1,
                grass_eaten BIGINT NOT NULL DEFAULT 0,
                distance_m  BIGINT NOT NULL DEFAULT 0,
                CONSTRAINT game_singleton CHECK (id = 1)
            )
            """
        )
        conn.execute("INSERT INTO game (id) VALUES (1) ON CONFLICT (id) DO NOTHING")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plants (
                id           SERIAL PRIMARY KEY,
                species      TEXT NOT NULL,
                emoji        TEXT NOT NULL,
                collected_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
