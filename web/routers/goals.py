"""
routers/goals.py - Goal CRUD endpoints for the Lakshya web API.
All endpoints require JWT authentication.
"""

from datetime import date, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import get_current_user
from database import get_connection
from models import (
    GoalCreateRequest,
    GoalResponse,
    ProgressRequest,
    MessageResponse,
    StreakItem,
)

router = APIRouter()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# -- Helpers ------------------------------------------------------------------

def _get_streak(goal_id: int) -> int:
    """Calculate current consecutive-day streak for a goal."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT completed_on FROM completions WHERE goal_id = ? ORDER BY completed_on DESC",
        (goal_id,),
    )
    rows = c.fetchall()
    conn.close()
    if not rows:
        return 0
    today = date.today()
    first = date.fromisoformat(rows[0]["completed_on"])
    if first != today and first != today - timedelta(days=1):
        return 0
    streak = 0
    check = first
    for row in rows:
        d = date.fromisoformat(row["completed_on"])
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


def _row_to_goal(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"] or "",
        "type": row["type"],
        "status": row["status"],
        "created_at": str(row["created_at"]),
        "progress": row["progress"] or 0,
    }


# -- Endpoints ----------------------------------------------------------------

@router.get("", response_model=List[GoalResponse])
def list_goals(
    type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all goals, optionally filtered by type and/or status."""
    conn = get_connection()
    c = conn.cursor()
    query = "SELECT id, title, description, type, status, created_at, progress FROM goals WHERE 1=1"
    params: list = []
    if type:
        query += " AND type = ?"
        params.append(type)
    if status:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return [_row_to_goal(r) for r in rows]


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    body: GoalCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Create a new goal."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO goals (title, description, type) VALUES (?, ?, ?)",
        (body.title, body.description or "", body.type),
    )
    conn.commit()
    goal_id = c.lastrowid
    c.execute(
        "SELECT id, title, description, type, status, created_at, progress FROM goals WHERE id = ?",
        (goal_id,),
    )
    row = c.fetchone()
    conn.close()
    return _row_to_goal(row)


@router.put("/{goal_id}/done", response_model=MessageResponse)
def mark_done(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Mark a goal as completed and record today in completions."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Goal #{goal_id} not found.")
    today = date.today().isoformat()
    c.execute("UPDATE goals SET status = 'completed' WHERE id = ?", (goal_id,))
    c.execute(
        "INSERT OR IGNORE INTO completions (goal_id, completed_on) VALUES (?, ?)",
        (goal_id, today),
    )
    conn.commit()
    conn.close()
    return {"message": f"Goal #{goal_id} marked as completed.", "ok": True}


@router.put("/{goal_id}/progress", response_model=MessageResponse)
def update_progress(
    goal_id: int,
    body: ProgressRequest,
    current_user: dict = Depends(get_current_user),
):
    """Update the progress percentage of a goal (0-100)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Goal #{goal_id} not found.")
    new_status = "completed" if body.percent >= 100 else "pending"
    c.execute(
        "UPDATE goals SET progress = ?, status = ? WHERE id = ?",
        (body.percent, new_status, goal_id),
    )
    if body.percent >= 100:
        today = date.today().isoformat()
        c.execute(
            "INSERT OR IGNORE INTO completions (goal_id, completed_on) VALUES (?, ?)",
            (goal_id, today),
        )
    conn.commit()
    conn.close()
    return {"message": f"Goal #{goal_id} progress set to {body.percent}%.", "ok": True}


@router.delete("/{goal_id}", response_model=MessageResponse)
def delete_goal(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
):
    """Delete a goal and all its completion records."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM goals WHERE id = ?", (goal_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Goal #{goal_id} not found.")
    c.execute("DELETE FROM completions WHERE goal_id = ?", (goal_id,))
    c.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return {"message": f"Goal #{goal_id} deleted.", "ok": True}


@router.get("/heatmap")
def get_heatmap(
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
):
    """Return {date: completion_count} for the last N days."""
    conn = get_connection()
    c = conn.cursor()
    start = (date.today() - timedelta(days=days)).isoformat()
    c.execute(
        "SELECT completed_on, COUNT(*) as cnt FROM completions WHERE completed_on >= ? GROUP BY completed_on",
        (start,),
    )
    rows = c.fetchall()
    conn.close()
    return {"data": {r["completed_on"]: r["cnt"] for r in rows}}


@router.get("/streaks", response_model=List[StreakItem])
def get_streaks(current_user: dict = Depends(get_current_user)):
    """Return streak count for every goal that has at least 1 completion."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, title FROM goals ORDER BY id")
    goals = c.fetchall()
    conn.close()
    result = []
    for g in goals:
        s = _get_streak(g["id"])
        if s > 0:
            result.append({"goal_id": g["id"], "title": g["title"], "streak": s})
    result.sort(key=lambda x: x["streak"], reverse=True)
    return result
