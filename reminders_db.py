"""
reminders_db.py -- SQLite layer for the Lakshya Reminders module.
Uses the same DB as the main app: ~/.lakshya/goals.db
"""

import os
import sqlite3
import subprocess

DB_PATH = os.path.join(os.path.expanduser("~"), ".lakshya", "goals.db")


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_reminders_db():
    conn = _get_conn()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id   INTEGER,
                label     TEXT    NOT NULL,
                remind_at TEXT    NOT NULL,
                days      TEXT    NOT NULL,
                active    INTEGER DEFAULT 1,
                task_name TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def add_reminder(label, remind_at, days, goal_id=None):
    conn = _get_conn()
    try:
        cur = conn.execute(
            "INSERT INTO reminders (goal_id, label, remind_at, days) VALUES (?, ?, ?, ?)",
            (goal_id, label, remind_at, days),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_task_name(reminder_id, task_name):
    conn = _get_conn()
    try:
        conn.execute("UPDATE reminders SET task_name = ? WHERE id = ?", (task_name, reminder_id))
        conn.commit()
    finally:
        conn.close()


def get_reminders():
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT * FROM reminders WHERE active = 1 ORDER BY id").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_reminder_by_id(reminder_id):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM reminders WHERE id = ? AND active = 1", (reminder_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_reminder(reminder_id):
    reminder = get_reminder_by_id(reminder_id)
    if not reminder:
        return False
    conn = _get_conn()
    try:
        conn.execute("UPDATE reminders SET active = 0 WHERE id = ?", (reminder_id,))
        conn.commit()
    finally:
        conn.close()
    task_name = reminder.get("task_name")
    if task_name:
        return unschedule_windows_task(task_name)
    return True


def schedule_windows_task(task_name, time_hh_mm, script_path, venv_python_path, message):
    safe_message = message.replace('"', "'")
    tr_value = '"{python}" "{script}" {msg}'.format(
        python=venv_python_path, script=script_path, msg=safe_message
    )
    cmd = ["schtasks", "/create", "/tn", task_name, "/tr", tr_value, "/sc", "DAILY", "/st", time_hh_mm, "/f"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def unschedule_windows_task(task_name):
    cmd = ["schtasks", "/delete", "/tn", task_name, "/f"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return True
        low = result.stderr.lower() + result.stdout.lower()
        if "cannot find" in low:
            return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
