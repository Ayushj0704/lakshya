"""
routers/timetable.py - Timetable endpoints for the Lakshya web API.
All endpoints require JWT authentication.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import get_current_user
from database import get_connection
from models import (
    TimetableSlotCreate,
    TimetableSlotResponse,
    ClashCheckRequest,
    MessageResponse,
)

router = APIRouter()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _row_to_slot(row) -> dict:
    return {
        "id": row["id"],
        "day": row["day_of_week"],
        "start": row["start_time"],
        "end": row["end_time"],
        "label": row["label"],
    }


@router.get("", response_model=List[TimetableSlotResponse])
def get_timetable(current_user: dict = Depends(get_current_user)):
    """Return all timetable slots ordered by day then start time."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, day_of_week, start_time, end_time, label FROM timetable ORDER BY day_of_week, start_time"
    )
    rows = c.fetchall()
    conn.close()
    return [_row_to_slot(r) for r in rows]


@router.post("", response_model=TimetableSlotResponse, status_code=status.HTTP_201_CREATED)
def add_slot(body: TimetableSlotCreate, current_user: dict = Depends(get_current_user)):
    """Add a new timetable slot."""
    if body.start_time >= body.end_time:
        raise HTTPException(status_code=400, detail="start_time must be before end_time.")
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO timetable (day_of_week, start_time, end_time, label) VALUES (?, ?, ?, ?)",
        (body.day_of_week, body.start_time, body.end_time, body.label),
    )
    conn.commit()
    slot_id = c.lastrowid
    c.execute(
        "SELECT id, day_of_week, start_time, end_time, label FROM timetable WHERE id = ?",
        (slot_id,),
    )
    row = c.fetchone()
    conn.close()
    return _row_to_slot(row)


@router.delete("/{slot_id}", response_model=MessageResponse)
def delete_slot(slot_id: int, current_user: dict = Depends(get_current_user)):
    """Delete a timetable slot by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM timetable WHERE id = ?", (slot_id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=f"Slot #{slot_id} not found.")
    c.execute("DELETE FROM timetable WHERE id = ?", (slot_id,))
    conn.commit()
    conn.close()
    return {"message": f"Slot #{slot_id} removed.", "ok": True}


@router.post("/check")
def check_clashes(body: ClashCheckRequest, current_user: dict = Depends(get_current_user)):
    """
    Check if the given day/start/end window clashes with existing timetable slots.
    Returns a list of clashing slots (may be empty).
    """
    if body.start >= body.end:
        raise HTTPException(status_code=400, detail="start must be before end.")
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, day_of_week, start_time, end_time, label FROM timetable WHERE day_of_week = ? ORDER BY start_time",
        (body.day,),
    )
    rows = c.fetchall()
    conn.close()
    clashes = []
    for r in rows:
        # Overlap: existing.start < new.end AND existing.end > new.start
        if r["start_time"] < body.end and r["end_time"] > body.start:
            clashes.append(_row_to_slot(r))
    return {
        "day": body.day,
        "day_name": DAY_NAMES[body.day],
        "start": body.start,
        "end": body.end,
        "clashes": clashes,
        "has_clashes": len(clashes) > 0,
    }
