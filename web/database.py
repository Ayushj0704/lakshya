"""
database.py - SQLite connection for the Lakshya web backend.
Reads/writes the SAME goals.db that the CLI uses.
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.expanduser("~"), ".lakshya", "goals.db")


def get_connection() -> sqlite3.Connection:
    """Return a connection to the Lakshya SQLite database."""
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_tables():
    """Create core tables if they don't exist (idempotent, mirrors db.py)."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            progress INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS completions (
            goal_id INTEGER,
            completed_on DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY(goal_id) REFERENCES goals(id),
            UNIQUE(goal_id, completed_on)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            label TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()
