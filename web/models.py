"""
models.py - Pydantic request/response models for the Lakshya web API.
"""

from typing import Optional
from pydantic import BaseModel, Field


# -- Auth ---------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: str


# -- Goals --------------------------------------------------------------------

class GoalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = ""
    type: str = Field(..., pattern="^(daily|weekly|monthly|yearly)$")


class ProgressRequest(BaseModel):
    percent: int = Field(..., ge=0, le=100)


class GoalResponse(BaseModel):
    id: int
    title: str
    description: str
    type: str
    status: str
    created_at: str
    progress: int


class StreakItem(BaseModel):
    goal_id: int
    title: str
    streak: int


# -- Timetable ----------------------------------------------------------------

class TimetableSlotCreate(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    label: str = Field(..., min_length=1, max_length=100)


class TimetableSlotResponse(BaseModel):
    id: int
    day: int
    start: str
    end: str
    label: str


class ClashCheckRequest(BaseModel):
    day: int = Field(..., ge=0, le=6)
    start: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end: str = Field(..., pattern=r"^\d{2}:\d{2}$")


# -- Generic ------------------------------------------------------------------

class MessageResponse(BaseModel):
    message: str
    ok: bool = True
