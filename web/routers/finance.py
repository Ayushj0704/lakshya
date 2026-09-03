"""
routers/finance.py - Finance stub for the Lakshya web API.
Full implementation activates automatically if finance_db.py exists in the project root.
"""

import os
import sys
from typing import List

from fastapi import APIRouter, Depends, HTTPException

# Adjust path so we can import from the web/ parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth import get_current_user

router = APIRouter()

# Try to import the real finance_db from the CLI project root
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_finance_available = False

if os.path.exists(os.path.join(_ROOT, "finance_db.py")):
    sys.path.insert(0, _ROOT)
    try:
        import finance_db as _fdb
        _finance_available = True
    except Exception:
        _finance_available = False


@router.get("")
def list_transactions(current_user: dict = Depends(get_current_user)):
    """List all finance transactions (requires finance_db.py in project root)."""
    if not _finance_available:
        return {
            "status": "stub",
            "message": "Finance module not yet available. Add finance_db.py to the project root to activate.",
            "transactions": [],
        }
    try:
        txns = _fdb.get_transactions()  # type: ignore[union-attr]
        return {"status": "ok", "transactions": txns}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/summary")
def finance_summary(current_user: dict = Depends(get_current_user)):
    """Return income/expense summary (requires finance_db.py)."""
    if not _finance_available:
        return {
            "status": "stub",
            "message": "Finance module not yet available.",
            "summary": {},
        }
    try:
        summary = _fdb.get_summary()  # type: ignore[union-attr]
        return {"status": "ok", "summary": summary}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

from pydantic import BaseModel

class TransactionCreate(BaseModel):
    amount: float
    txn_type: str  # 'income' or 'expense'
    category: str
    note: str = ""

@router.post("")
def add_transaction(txn: TransactionCreate, current_user: dict = Depends(get_current_user)):
    """Add a transaction."""
    if not _finance_available:
        raise HTTPException(status_code=501, detail="Finance module not available.")
    try:
        rid = _fdb.add_transaction(txn.amount, txn.txn_type, txn.category, txn.note)
        return {"status": "ok", "id": rid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
