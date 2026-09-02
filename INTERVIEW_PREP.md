# Lakshya — Interview Preparation Guide

> Use this document to prepare for technical interviews where you discuss this project.
> Read it before the interview. The goal is to sound like someone who **made real decisions**, not just someone who wrote code.

---

## 1. The Elevator Pitch (30 seconds)

Practice saying this out loud:

> "Lakshya is a terminal-based goal management engine I built in Python. I noticed that every mainstream productivity app either requires a subscription, only works online, or is bloated with features I don't need. So I built a minimalist CLI tool that lets you manage daily habits, weekly goals, and long-term yearly objectives — entirely offline, with a local SQLite database. It has an interactive shell, a GitHub-style activity heatmap, streak tracking, a Pomodoro timer, a college timetable manager with clash detection, and a dancing cat animation when you complete a goal."

The last part always gets a laugh and makes you memorable.

---

## 2. Tech Stack — What You Used and Why

| Technology | Why you chose it |
|---|---|
| **Python** | Rapid prototyping, rich CLI ecosystem, cross-platform |
| **Click** | Most mature Python CLI framework — handles args, flags, prompts, nested command groups cleanly |
| **Rich** | Best Python library for terminal UI — tables, progress bars, panels, spinners, live rendering |
| **SQLite** (`sqlite3` stdlib) | Zero-configuration, serverless, file-based — perfect for a local desktop tool. No ORM overhead |
| **`difflib`** (stdlib) | Powers the fuzzy command suggester — pure standard library, no extra dependency |
| **`shlex`** (stdlib) | Safely parses user input strings into argument lists inside the REPL shell |
| **Virtual Environment (`venv`)** | Isolates project dependencies from the system Python — industry standard practice |

---

## 3. Architecture — The Two-Layer Design

This is the most important thing to explain clearly in an interview.

```
┌─────────────────────────────────┐
│   Presentation Layer            │
│   lakshya.py                    │
│   ─ Click commands              │
│   ─ Rich UI (tables, spinners)  │
│   ─ Interactive REPL shell      │
│   ─ Animations                  │
└────────────────┬────────────────┘
                 │ calls
┌────────────────▼────────────────┐
│   Data Access Layer             │
│   db.py                         │
│   ─ SQLite connection manager   │
│   ─ CRUD for goals              │
│   ─ Completions / streaks       │
│   ─ Timetable + clash logic     │
│   ─ CSV export                  │
└─────────────────────────────────┘
                 │
┌────────────────▼────────────────┐
│   ~\.lakshya\goals.db           │
│   (SQLite file on disk)         │
└─────────────────────────────────┘
```

**Why this matters:** Separating the UI layer from the data layer means you can swap out the frontend (e.g., replace the CLI with a web API) without touching any database logic. This is the same principle used in production apps — it's called the Repository Pattern or DAL (Data Access Layer).

---

## 4. Database Schema

Three tables. Know them cold.

```sql
-- Stores all goals
CREATE TABLE goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    description TEXT DEFAULT '',
    type        TEXT NOT NULL,        -- 'daily', 'weekly', 'monthly', 'yearly'
    status      TEXT DEFAULT 'pending', -- 'pending' or 'completed'
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    progress    INTEGER DEFAULT 0     -- 0-100, for monthly/yearly goals
);

-- One row per (goal, day) when a goal is completed — powers heatmap + streaks
CREATE TABLE completions (
    goal_id      INTEGER,
    completed_on DATE DEFAULT CURRENT_DATE,
    FOREIGN KEY(goal_id) REFERENCES goals(id),
    UNIQUE(goal_id, completed_on)      -- prevents double-counting
);

-- College / work timetable slots
CREATE TABLE timetable (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week INTEGER NOT NULL,      -- 0=Monday ... 6=Sunday
    start_time  TEXT NOT NULL,         -- 'HH:MM' 24h format
    end_time    TEXT NOT NULL,
    label       TEXT NOT NULL
);
```

---

## 5. Key Algorithms — Be Ready to Explain These

### A. Streak Calculation

**Q: How does the streak counter work?**

> "When a user completes a daily goal, I insert a row into the `completions` table with today's date. To calculate the streak, I fetch all completion dates for that goal in descending order. I then walk backwards from today (or yesterday, if it hasn't been completed today yet). For each step, if the date matches the expected date, I increment the counter. As soon as there's a gap, the loop breaks. This is O(n) in the number of completion records."

```python
def get_streak(goal_id):
    rows = fetch_completions_desc(goal_id)  # ['2026-09-03', '2026-09-02', ...]
    today = date.today()
    first = date.fromisoformat(rows[0][0])
    # Allow today OR yesterday as the starting point
    if first != today and first != today - timedelta(days=1):
        return 0  # Streak is already broken
    check = first
    streak = 0
    for row in rows:
        if date.fromisoformat(row[0]) == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak
```

### B. Activity Heatmap

**Q: How did you build the heatmap?**

> "I query the `completions` table grouped by `completed_on` for the last N days and get a count per date. I then iterate over every day in the range. If the count is 0, I render a dim dot. If it's 1, a green `o`. If 2-3, a bright `*`. If 4+, a blue `#`. I arrange these into rows of 7 columns for the monthly view (one column per weekday) and 30 columns for the yearly view. The result looks like GitHub's contribution graph."

### C. Timetable Clash Detection

**Q: How does clash detection work?**

> "Two time intervals [A_start, A_end] and [B_start, B_end] overlap if and only if `A_start < B_end AND A_end > B_start`. This is the standard interval overlap formula. When the user provides a planned time slot, I run this check against every timetable entry for that day of the week and return any matches."

```python
def check_timetable_clash(day, check_start, check_end):
    slots = get_timetable(day_of_week=day)
    return [s for s in slots if s["start"] < check_end and s["end"] > check_start]
```

### D. Fuzzy Command Matching

**Q: How did you implement the typo suggester?**

> "I subclassed Click's `Group` class and overrode `get_command()`. If a command isn't found exactly, I call Python's `difflib.get_close_matches()` from the standard library against the list of all registered commands. If there's a close match, I print a suggestion. It's a single function, zero extra dependencies."

---

## 6. Virtual Environment — Why It Matters

**Q: Why did you use a virtual environment?**

> "Python installs packages globally by default. If two projects need different versions of the same library — say, `click==7` for one and `click==8` for another — they'll conflict and break each other. A virtual environment (`venv`) creates an isolated Python installation per project with its own `site-packages` folder. This is standard practice in any Python project.
>
> In Lakshya, I used `venv` so that `click` and `rich` are installed only for this project. The `install.bat` script creates the venv, installs dependencies into it, and then uses `pip install -e .` (editable install) to register the `lakshya` command globally within that environment."

**Q: What does `pip install -e .` do?**

> "The `-e` flag stands for 'editable install'. It tells pip to install the package in development mode — meaning it creates a symlink to the source files instead of copying them. So any change I make to `lakshya.py` is immediately reflected when I run the `lakshya` command, without needing to reinstall. It's the equivalent of `npm link` in Node.js."

**Q: What's the difference between the venv's pip and the system pip?**

> "The venv has its own copy of `pip` at `venv/Scripts/pip.exe`. Using this pip installs packages only inside the venv. Using the system pip would install them globally, potentially affecting other projects. The `lakshya.bat` file hard-codes the path to the venv's Python interpreter so it always uses the right environment regardless of what's activated in the shell."

---

## 7. Common Interview Questions — Full Answers

**Q: Why SQLite instead of a proper database like PostgreSQL?**

> "Lakshya is a local desktop tool. There's no server, no concurrent users, no network. SQLite is the right tool — it's a file on disk, requires zero configuration, and is part of Python's standard library. It handles everything I need: transactions, foreign keys, and GROUP BY queries for the heatmap. Using PostgreSQL would add unnecessary operational complexity."

**Q: Why not use an ORM like SQLAlchemy?**

> "For a project this small, raw SQL is cleaner and more transparent. I write exactly the queries I need and can optimize them directly. With an ORM, I'd spend time fighting abstractions for something as simple as a `GROUP BY completed_on` query. I also used parameterized queries (`?` placeholders) throughout, which prevents SQL injection — so security isn't sacrificed."

**Q: How do you handle backward compatibility when the schema changes?**

> "In `init_db()`, I use `CREATE TABLE IF NOT EXISTS` for all tables so existing databases aren't affected on upgrade. When I added the `progress` column after the initial release, I used `PRAGMA table_info(goals)` to check if the column existed and only ran `ALTER TABLE` if it was missing. This is a simple schema migration strategy — for a larger project, I'd use a tool like Alembic."

**Q: What's the biggest limitation and what would Phase 2 look like?**

> "The biggest limitation is that it's local to one machine. Phase 2 would be a cloud sync layer: a FastAPI backend with JWT token authentication, syncing the local SQLite data to a PostgreSQL database. A React or Next.js frontend could then give you a web dashboard accessible from any device. The CLI would remain the primary interface for power users, but the web app would handle mobile access and sharing."

**Q: How would you add user authentication to the CLI?**

> "I'd store a JWT token in a config file at `~/.lakshya/config.json` after a one-time `lakshya login` command. On every subsequent request, the token would be attached to the API call. The `init_db()` step would check token validity and refresh it if expired — similar to how the AWS CLI handles credentials."

**Q: What design patterns did you use?**

> "Primarily the Repository Pattern — `db.py` is a repository that abstracts all data access behind named functions. The CLI layer never writes SQL directly. I also used the Command Pattern implicitly through Click's command routing. The interactive REPL is a classic Read-Eval-Print Loop."

---

## 8. What to Say When They Ask "Walk Me Through The Code"

Start with the big picture:

1. **Entry point:** `lakshya.bat` calls `venv/Scripts/python.exe lakshya.py`. When run without arguments, it shows the splash screen and starts the REPL loop.
2. **REPL loop:** `interactive_mode()` reads input with `rich.prompt.Prompt.ask()`, parses it with `shlex.split()`, and re-invokes the Click CLI with those args via `cli.main(args=..., standalone_mode=False)`.
3. **Command routing:** Click's `FuzzyGroup` subclass intercepts unrecognised commands and runs `difflib.get_close_matches()` before returning `None`.
4. **Data layer:** Every command calls functions in `db.py`. `get_connection()` creates a fresh SQLite connection each time (appropriate for a single-user local app).
5. **Heatmap:** `get_heatmap_data()` runs a `GROUP BY` query, returns a `{date_string: count}` dict, and the CLI renders it as a grid.

---

## 9. Numbers to Remember

| Metric | Value |
|---|---|
| Lines of code | ~500 (lakshya.py) + ~220 (db.py) |
| External dependencies | 2 (`click`, `rich`) |
| Database tables | 3 (`goals`, `completions`, `timetable`) |
| CLI commands | 14 |
| Time to first goal | < 5 seconds from launch |

---

## 10. CV One-Liner

> **Lakshya** — Terminal Productivity Engine | *Python, SQLite, Click, Rich* | [github.com/yourhandle/lakshya]
>
> Built a full-featured CLI goal manager with interactive REPL shell, streak tracking, GitHub-style activity heatmap, Pomodoro focus timer, college timetable manager with interval overlap clash detection, animated goal completion, and one-command installation via pip editable install.
