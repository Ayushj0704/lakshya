"""
finance_db.py  --  Data layer for Lakshya Finance Tracker
Uses the same goals.db as the main app.
All strings are ASCII-safe for Windows cp1252 terminals.
"""

import sqlite3
import os
from datetime import date

DB_FILE = os.path.join(os.path.expanduser("~"), ".lakshya", "goals.db")


# -- Connection helper ---------------------------------------------------------

def _get_conn():
    db_dir = os.path.dirname(DB_FILE)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


# -- Schema init ---------------------------------------------------------------

def init_finance_db():
    """Create transactions and budgets tables if they do not exist."""
    conn = _get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            amount      REAL    NOT NULL,
            type        TEXT    NOT NULL CHECK(type IN ('income', 'expense')),
            category    TEXT    NOT NULL DEFAULT 'other',
            note        TEXT    DEFAULT '',
            date        DATE    NOT NULL DEFAULT CURRENT_DATE,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            category      TEXT    NOT NULL UNIQUE,
            monthly_limit REAL    NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# -- Transactions --------------------------------------------------------------

def add_transaction(amount, txn_type, category, note=""):
    """Insert a transaction for today. txn_type must be 'income' or 'expense'."""
    conn = _get_conn()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute(
        "INSERT INTO transactions (amount, type, category, note, date) VALUES (?, ?, ?, ?, ?)",
        (float(amount), txn_type, category.lower(), note, today)
    )
    conn.commit()
    txn_id = c.lastrowid
    conn.close()
    return txn_id


def get_transactions(month=None, year=None):
    """
    Return list of dicts for transactions in the given month/year.
    Defaults to the current month and year.
    """
    today = date.today()
    month = month or today.month
    year  = year  or today.year

    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """
        SELECT id, amount, type, category, note, date, created_at
        FROM   transactions
        WHERE  strftime('%Y', date) = ?
          AND  strftime('%m', date) = ?
        ORDER  BY date DESC, id DESC
        """,
        (str(year), f"{month:02d}")
    )
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_transaction(txn_id):
    """Delete a transaction by its ID. Returns True if a row was removed."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE id = ?", (txn_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


# -- Budgets ------------------------------------------------------------------

def set_budget(category, limit):
    """Upsert a monthly budget limit for a category."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO budgets (category, monthly_limit) VALUES (?, ?)
        ON CONFLICT(category) DO UPDATE SET monthly_limit = excluded.monthly_limit
        """,
        (category.lower(), float(limit))
    )
    conn.commit()
    conn.close()


def get_budgets():
    """Return all budget rows as a list of dicts."""
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT id, category, monthly_limit FROM budgets ORDER BY category")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# -- Summary ------------------------------------------------------------------

def get_summary(month=None, year=None):
    """
    Return a summary dict for the given month/year (defaults to current month).

    Shape:
        {
            "total_income":   float,
            "total_expenses": float,
            "net":            float,
            "per_category":   {
                category: {
                    "spent":  float,
                    "budget": float | None,
                    "pct":    float   # 0-100+; 0 if no budget set
                }
            }
        }
    """
    txns    = get_transactions(month=month, year=year)
    budgets = {b["category"]: b["monthly_limit"] for b in get_budgets()}

    total_income   = 0.0
    total_expenses = 0.0
    cat_spending   = {}

    for t in txns:
        if t["type"] == "income":
            total_income += t["amount"]
        else:
            total_expenses += t["amount"]
            cat = t["category"]
            cat_spending[cat] = cat_spending.get(cat, 0.0) + t["amount"]

    # Include categories that have a budget even if nothing was spent
    all_cats = set(cat_spending.keys()) | set(budgets.keys())
    per_category = {}
    for cat in sorted(all_cats):
        spent  = cat_spending.get(cat, 0.0)
        budget = budgets.get(cat, None)
        pct    = (spent / budget * 100.0) if budget else 0.0
        per_category[cat] = {"spent": spent, "budget": budget, "pct": pct}

    return {
        "total_income":   total_income,
        "total_expenses": total_expenses,
        "net":            total_income - total_expenses,
        "per_category":   per_category,
    }


# -- Savings Goals (linked to main goals table) --------------------------------

def add_savings_goal(title, target_amount):
    """
    Create a yearly goal in the main goals table with description
    'savings:TARGET_AMOUNT' so the main app can detect it as a savings entry.
    Returns the new goal id.
    """
    conn = _get_conn()
    c = conn.cursor()
    description = f"savings:{float(target_amount)}"
    c.execute(
        "INSERT INTO goals (title, description, type) VALUES (?, ?, 'yearly')",
        (title, description)
    )
    conn.commit()
    goal_id = c.lastrowid
    conn.close()
    return goal_id
