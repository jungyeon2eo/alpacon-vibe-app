import os

import psycopg

DATABASE_URL = os.environ["DATABASE_URL"]


def get_conn():
    """Open a short-lived autocommit connection."""
    return psycopg.connect(DATABASE_URL, autocommit=True)


def init_db():
    """Create per-player game tables. Idempotent; migrates the old single-player schema once."""
    with get_conn() as conn:
        # legacy single-player table (pre per-player) — no longer used
        conn.execute("DROP TABLE IF EXISTS game")
        # if an old plants table exists without player_id, it's legacy test data — drop once
        conn.execute(
            """
            DO $$
            BEGIN
              IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='plants')
                 AND NOT EXISTS (SELECT 1 FROM information_schema.columns
                                 WHERE table_name='plants' AND column_name='player_id') THEN
                DROP TABLE plants;
              END IF;
            END $$;
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS players (
                id          TEXT PRIMARY KEY,
                pin_hash    TEXT NOT NULL,
                salt        TEXT NOT NULL,
                grass_eaten BIGINT NOT NULL DEFAULT 0,
                distance_m  BIGINT NOT NULL DEFAULT 0,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS plants (
                id           SERIAL PRIMARY KEY,
                player_id    TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                species      TEXT NOT NULL,
                emoji        TEXT NOT NULL,
                collected_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS plants_player_idx ON plants (player_id)")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                id         SERIAL PRIMARY KEY,
                player_id  TEXT NOT NULL REFERENCES players(id) ON DELETE CASCADE,
                name       TEXT NOT NULL,
                distance_m BIGINT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS checkpoints_player_idx ON checkpoints (player_id)")
