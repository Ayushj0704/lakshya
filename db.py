import sqlite3
from datetime import datetime, date, timedelta
import os
import csv

DB_FILE = os.path.join(os.path.expanduser("~"), ".lakshya", "goals.db")


def get_connection():
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return sqlite3.connect(DB_FILE)


def init_db():
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

    # Timetable: each slot is day_of_week (0=Mon..6=Sun), start_time, end_time, label
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


def add_goal(title, description, goal_type):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO goals (title, description, type) VALUES (?, ?, ?)",
              (title, description, goal_type))
    conn.commit()
    goal_id = c.lastrowid
    conn.close()
    return goal_id


def get_goals(goal_type=None, status=None):
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT id, title, description, type, status, created_at, progress FROM goals WHERE 1=1"
    params = []
    if goal_type:
        query += " AND type = ?"
        params.append(goal_type)
    if status:
        query += " AND status = ?"
        params.append(status)
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "description": r[2], "type": r[3],
             "status": r[4], "created_at": r[5], "progress": r[6] or 0}
            for r in rows]


def get_goal_by_id(goal_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title, description, type, status, created_at, progress FROM goals WHERE id=?", (goal_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "title": row[1], "description": row[2], "type": row[3],
                "status": row[4], "created_at": row[5], "progress": row[6] or 0}
    return None


def update_goal_status(goal_id, status):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE goals SET status = ? WHERE id = ?", (status, goal_id))
    today = date.today().isoformat()
    if status == 'completed':
        c.execute("INSERT OR IGNORE INTO completions (goal_id, completed_on) VALUES (?, ?)", (goal_id, today))
    else:
        c.execute("DELETE FROM completions WHERE goal_id = ? AND completed_on = ?", (goal_id, today))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def update_progress(goal_id, progress):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE goals SET progress = ? WHERE id = ?", (progress, goal_id))
    if progress >= 100:
        c.execute("UPDATE goals SET status = 'completed' WHERE id = ?", (goal_id,))
    else:
        c.execute("UPDATE goals SET status = 'pending' WHERE id = ?", (goal_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def delete_goal(goal_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM completions WHERE goal_id = ?", (goal_id,))
    c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def get_streak(goal_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT completed_on FROM completions WHERE goal_id = ? ORDER BY completed_on DESC", (goal_id,))
    rows = c.fetchall()
    conn.close()
    if not rows:
        return 0
    today = date.today()
    first = date.fromisoformat(rows[0][0])
    if first != today and first != today - timedelta(days=1):
        return 0
    streak = 0
    check = first
    for row in rows:
        d = date.fromisoformat(row[0])
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


def get_heatmap_data(days=30):
    conn = get_connection()
    c = conn.cursor()
    start = (date.today() - timedelta(days=days)).isoformat()
    c.execute("SELECT completed_on, COUNT(*) FROM completions WHERE completed_on >= ? GROUP BY completed_on", (start,))
    rows = c.fetchall()
    conn.close()
    return {r[0]: r[1] for r in rows}


def export_to_csv(filepath):
    goals = get_goals()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Title', 'Description', 'Type', 'Status', 'Progress', 'Created At'])
        for g in goals:
            writer.writerow([g['id'], g['title'], g['description'], g['type'],
                             g['status'], g['progress'], g['created_at']])


# ── Timetable ─────────────────────────────────────────────────────────────────

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def add_timetable_slot(day_of_week, start_time, end_time, label):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO timetable (day_of_week, start_time, end_time, label) VALUES (?, ?, ?, ?)",
              (day_of_week, start_time, end_time, label))
    conn.commit()
    slot_id = c.lastrowid
    conn.close()
    return slot_id


def get_timetable(day_of_week=None):
    conn = get_connection()
    c = conn.cursor()
    if day_of_week is not None:
        c.execute("SELECT id, day_of_week, start_time, end_time, label FROM timetable WHERE day_of_week=? ORDER BY start_time", (day_of_week,))
    else:
        c.execute("SELECT id, day_of_week, start_time, end_time, label FROM timetable ORDER BY day_of_week, start_time")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "day": r[1], "start": r[2], "end": r[3], "label": r[4]} for r in rows]


def delete_timetable_slot(slot_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM timetable WHERE id = ?", (slot_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def check_timetable_clash(check_day, check_start, check_end):
    """Returns list of clashing timetable slots for a given day and time window."""
    slots = get_timetable(day_of_week=check_day)
    clashes = []
    for s in slots:
        # Overlap condition: s.start < check_end AND s.end > check_start
        if s["start"] < check_end and s["end"] > check_start:
            clashes.append(s)
    return clashes
