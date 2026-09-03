"""
main.py - FastAPI application entry point for the Lakshya web backend.
Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import os
import sys

# Ensure web/ directory is on the path so imports resolve cleanly
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import auth
import database
from auth import get_current_user
from models import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
)
from routers import goals, timetable, finance

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Lakshya API",
    version="1.0.0",
    description="REST backend for the Lakshya goal-tracking engine.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (index.html dashboard)
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Include routers
app.include_router(goals.router,     prefix="/api/goals",     tags=["Goals"])
app.include_router(timetable.router, prefix="/api/timetable", tags=["Timetable"])
app.include_router(finance.router,   prefix="/api/finance",   tags=["Finance"])

# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def startup():
    database.ensure_tables()
    auth.init_auth_db()


# ---------------------------------------------------------------------------
# Auth endpoints
# ---------------------------------------------------------------------------

@app.post("/api/auth/register", response_model=UserResponse, status_code=201, tags=["Auth"])
def register(body: RegisterRequest):
    """Create a new Lakshya web account."""
    try:
        user = auth.create_user(body.username, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    full = auth.get_user(user["username"])
    return {
        "id": full["id"],
        "username": full["username"],
        "created_at": str(full["created_at"]),
    }


@app.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(body: LoginRequest):
    """Authenticate and receive a JWT access token."""
    user = auth.authenticate_user(body.username, body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )
    token = auth.create_token(user["username"])
    return {"access_token": token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse, tags=["Auth"])
def me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "created_at": str(current_user["created_at"]),
    }


# ---------------------------------------------------------------------------
# Root - serve dashboard
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    """Serve the single-page dashboard."""
    index = os.path.join(_STATIC_DIR, "index.html")
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "Lakshya API is running. See /docs for the interactive API docs."}
