import sqlite3
from datetime import datetime, date
from typing import Optional, Iterable
from config import DB_PATH

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(r[1] == column for r in cur.fetchall())

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                city TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                timezone TEXT NOT NULL,
                lang TEXT NOT NULL DEFAULT 'en',
                created_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                notified INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        if not column_exists(conn, "users", "timezone"):
            conn.execute("ALTER TABLE users ADD COLUMN timezone TEXT NOT NULL DEFAULT 'UTC'")
        if not column_exists(conn, "users", "lang"):
            conn.execute("ALTER TABLE users ADD COLUMN lang TEXT NOT NULL DEFAULT 'en'")
        conn.commit()

def set_user_city(user_id: int, city: str, lat: float, lon: float, timezone: str):
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, city, lat, lon, timezone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET city=excluded.city, lat=excluded.lat, lon=excluded.lon, timezone=excluded.timezone
        """, (user_id, city, lat, lon, timezone, datetime.now().isoformat()))
        conn.commit()

def set_user_lang(user_id: int, lang: str):
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, city, lat, lon, timezone, lang, created_at)
            VALUES (?, '', 0, 0, 'UTC', ?, ?)
            ON CONFLICT(user_id) DO UPDATE
            SET lang=excluded.lang
        """, (user_id, lang, datetime.now().isoformat()))
        conn.commit()

def get_user(user_id: int) -> Optional[sqlite3.Row]:
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

def list_all_users() -> Iterable[sqlite3.Row]:
    with db() as conn:
        return conn.execute("SELECT user_id, city, lat, lon, timezone, lang FROM users").fetchall()

def add_event(user_id: int, title: str, event_date: date) -> int:
    with db() as conn:
        cur = conn.execute("""
            INSERT INTO events (user_id, title, event_date, created_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, title, event_date.isoformat(), datetime.utcnow().isoformat()))
        conn.commit()
        return cur.lastrowid

def list_events(user_id: int):
    with db() as conn:
        return conn.execute("""
            SELECT id, title, event_date, notified
            FROM events
            WHERE user_id = ?
            ORDER BY event_date ASC
        """, (user_id,)).fetchall()

def delete_event(user_id: int, event_id: int) -> bool:
    with db() as conn:
        cur = conn.execute("DELETE FROM events WHERE id = ? AND user_id = ?", (event_id, user_id))
        conn.commit()
        return cur.rowcount > 0

def get_events_for_date(user_id: int, day_iso: str) -> list[sqlite3.Row]:
    with db() as conn:
        return conn.execute("""
            SELECT id, title, event_date, notified
            FROM events
            WHERE user_id = ? AND event_date = ? AND notified = 0
        """, (user_id, day_iso)).fetchall()

def mark_notified(event_id: int):
    with db() as conn:
        conn.execute("UPDATE events SET notified = 1 WHERE id = ?", (event_id,))
        conn.commit()
