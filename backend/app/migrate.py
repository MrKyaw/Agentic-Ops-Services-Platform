"""Versioned SQL migration runner. Applies pending *.sql files in order, records versions."""

from pathlib import Path

import psycopg

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _ensure_table(conn: psycopg.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations "
        "(version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )


def pending(url: str) -> list[str]:
    files = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    with psycopg.connect(url) as conn:
        _ensure_table(conn)
        applied = {
            r[0]
            for r in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }
    return [f for f in files if f not in applied]


def migrate(url: str) -> list[str]:
    files = sorted(p.name for p in MIGRATIONS_DIR.glob("*.sql"))
    applied_now: list[str] = []
    with psycopg.connect(url) as conn:
        _ensure_table(conn)
        done = {
            r[0]
            for r in conn.execute("SELECT version FROM schema_migrations").fetchall()
        }
        for name in files:
            if name in done:
                continue
            sql = (MIGRATIONS_DIR / name).read_text(encoding="utf-8")
            conn.execute(sql)
            conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (name,))
            applied_now.append(name)
        conn.commit()
    return applied_now
