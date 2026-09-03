"""
auth.py - JWT-based authentication for the Lakshya web API.
Uses sha256 password hashing (no bcrypt) and PyJWT for tokens.
"""

import hashlib
import sqlite3
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from database import get_connection

SECRET_KEY = "lakshya-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# -- DB setup ------------------------------------------------------------------

def init_auth_db():
    """Create the users table if it doesn't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


# -- Password helpers ----------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return hex-encoded sha256 digest of the plaintext password."""
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Compare sha256 of plain against stored hash."""
    return hash_password(plain) == hashed


# -- User CRUD ----------------------------------------------------------------

def create_user(username: str, plain_password: str) -> dict:
    """Insert a new user. Raises ValueError if username already taken."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hash_password(plain_password)),
        )
        conn.commit()
        user_id = c.lastrowid
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Username '{username}' is already taken.")
    conn.close()
    return {"id": user_id, "username": username}


def get_user(username: str) -> dict | None:
    """Fetch user row by username. Returns dict or None."""
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT id, username, hashed_password, created_at FROM users WHERE username = ?",
        (username,),
    )
    row = c.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def authenticate_user(username: str, plain_password: str) -> dict | None:
    """Return user dict if credentials are valid, else None."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(plain_password, user["hashed_password"]):
        return None
    return user


# -- JWT helpers --------------------------------------------------------------

def create_token(username: str) -> str:
    """Create a signed JWT that expires in TOKEN_EXPIRE_HOURS hours."""
    expire = datetime.now(tz=timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> str:
    """Decode JWT and return the username. Raises HTTPException on failure."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise ValueError("Token missing subject claim.")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired."
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {exc}"
        )


# -- FastAPI dependency -------------------------------------------------------

def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """FastAPI dependency: validates JWT and returns the user dict."""
    username = decode_token(token)
    user = get_user(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found."
        )
    return user
