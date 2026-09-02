# Lakshya (लक्ष्य) — The Minimalist Goal Engine

> *lak·shya* — Sanskrit for **target, aim, goal**

Lakshya is a fast, keyboard-first, terminal-based productivity engine built in Python.
No internet. No subscriptions. No distractions. Just you and your goals.

---

## Why Lakshya?

Most goal-tracking apps are bloated, subscription-walled, and built for phones — not for developers who live in the terminal. Lakshya runs entirely offline using a local SQLite database. It starts in under a second and gets out of your way.

---

## Features

| Feature | Description |
|---|---|
| **Interactive Shell** | Launch with no args to enter the `lakshya>` REPL prompt |
| **Colorful Splash Screen** | Rainbow ASCII art banner on every launch |
| **4 Goal Types** | `daily`, `weekly`, `monthly`, `yearly` |
| **Quick-Add Shortcuts** | `day`, `week`, `month`, `year` commands — no typing long flags |
| **Fuzzy Command Matching** | Typo `progess`? It suggests `progress` automatically |
| **Progress Bars** | Visual `[========--]` bars for monthly/yearly goals |
| **Streak Tracking** | Counts consecutive days you completed a daily habit |
| **Activity Heatmap** | GitHub-style 30-day or 365-day consistency grid |
| **Dancing Cat Animation** | A cat dances in your terminal when you complete a goal |
| **Focus Timer (Pomodoro)** | Built-in countdown timer with live progress bar |
| **Timetable Manager** | Add your college schedule and detect goal-time clashes |
| **Export** | Export all goals to CSV or Markdown |
| **Local SQLite Storage** | All data stored in `~/.lakshya/goals.db` — 100% private |

---

## Installation

### One-time setup (like `npm install`)

```powershell
# 1. Clone or open the project folder
cd path\to\gola

# 2. Run the installer (creates venv, installs deps, registers global command)
.\install.bat

# 3. Activate the virtual environment
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\venv\Scripts\Activate.ps1

# 4. Launch!
lakshya
```

> After the venv is activated, you can just type `lakshya` from anywhere — no `.\` prefix needed.

---

## Usage

### Launch Interactive Shell
```powershell
.\lakshya.bat
# or (after global install + venv activated):
lakshya
```

You'll see the splash screen and drop into the `lakshya>` prompt. Type `help` at any time.

---

## Commands

### Adding Goals

```bash
# Full interactive add (prompts you step by step):
lakshya> add

# Inline with flags:
lakshya> add "Read 20 pages" --type daily
lakshya> add "Launch side project" --type yearly --desc "Ship by December"

# Quick-add shortcuts (no --type flag needed):
lakshya> day      # Create a daily task
lakshya> week     # Create a weekly goal
lakshya> month    # Create a monthly goal
lakshya> year     # Create a yearly goal
```

### Viewing Goals

```bash
lakshya> ls                    # All goals
lakshya> ls --type daily       # Filter by type
lakshya> ls --type yearly
lakshya> ls --status pending   # Filter by status
lakshya> ls --status completed
```

The table shows:
- **[v]** for completed, **[ ]** for pending
- A visual progress bar `[========--] 80%` for monthly/yearly goals
- A streak counter `3 day streak!` for daily habits

### Completing Goals

```bash
lakshya> done 5
```

Triggers a **dancing cat animation** for ~2 seconds, then shows a bold celebration banner.

### Updating Progress (Monthly / Yearly)

```bash
lakshya> progress 3 50    # Set goal #3 to 50% complete
lakshya> progress 3 100   # Auto-marks as completed
```

### Undo / Delete

```bash
lakshya> undo 5    # Revert completed goal back to pending
lakshya> rm 5      # Permanently delete a goal
```

---

## Activity Heatmap

```bash
lakshya> heatmap          # Prompts for m(onth) or y(ear)
lakshya> heatmap -p m     # Direct 30-day view
lakshya> heatmap -p y     # Direct 365-day year view
```

Legend: `. = none`, `o = 1`, `* = 2-3`, `# = 4+ completions`

The grid shows:
- **Month view**: 7-column grid with Mon–Sun weekday headers, date range in title
- **Year view**: 30-column grid spanning the last 365 days

---

## Focus Timer (Pomodoro)

```bash
lakshya> clock               # Prompts for minutes (default 25)
lakshya> clock --minutes 25  # Full Pomodoro session
lakshya> clock --minutes 5   # Short break timer
lakshya> clock --minutes 0.1 # 6-second test
```

Shows a live animated progress bar with time remaining.

---

## Timetable (College / Work Schedule)

Add your recurring schedule so Lakshya can warn you when a planned task clashes with a class or meeting.

```bash
# Add a class slot
lakshya> tt add
# → Day: 0 (Monday), Start: 09:00, End: 10:30, Label: Data Structures

# View your timetable
lakshya> tt ls              # All days
lakshya> tt ls --day 0      # Monday only

# Check if a planned time is free
lakshya> tt check
# → Enter day + time window → Lakshya warns you of any clash

# Remove a slot
lakshya> tt rm 1
```

Day mapping: `0=Mon  1=Tue  2=Wed  3=Thu  4=Fri  5=Sat  6=Sun`

---

## Export

```bash
lakshya> export --format csv       # → lakshya_export.csv
lakshya> export --format markdown  # → lakshya_export.md
```

---

## Fuzzy Command Suggestions

Lakshya catches typos and suggests the closest real command:
```
lakshya> progess    →  Tip: Did you mean 'progress'?
lakshya> donne      →  Tip: Did you mean 'done'?
lakshya> heatmapp   →  Tip: Did you mean 'heatmap'?
```

---

## Project Structure

```
gola/
├── lakshya.py        # CLI commands, UI, animations (Rich + Click)
├── db.py             # SQLite data access layer (goals + timetable)
├── setup.py          # Package config for global `lakshya` command
├── install.bat       # One-click installer
├── lakshya.bat       # Quick runner (no global install needed)
├── README.md         # This file
└── INTERVIEW_PREP.md # Interview Q&A guide for CV
```

Data is stored at: `C:\Users\<you>\.lakshya\goals.db`

---

## Tech Stack

- **Python 3.8+**
- **[Click](https://click.palletsprojects.com/)** — CLI framework (commands, arguments, prompts)
- **[Rich](https://github.com/Textar/rich)** — Terminal UI (tables, panels, spinners, progress bars, live rendering)
- **SQLite** (via Python's built-in `sqlite3`) — local database, zero config

---

## Why I Built This

> "Most goal apps are designed for people who want to feel productive. Lakshya is built for people who want to **be** productive."

I built Lakshya because every existing tool either required a subscription, didn't work offline, or had too much clutter. By moving goal management to the terminal, it becomes a frictionless part of a developer's existing workflow — no browser tabs, no ads, no accounts.

---

## CV Description

> **Lakshya** — Terminal Productivity Engine *(Python, SQLite, Click, Rich)*
>
> Built a full-featured CLI application with an interactive REPL shell, streak tracking, GitHub-style activity heatmaps, a Pomodoro focus timer, college timetable manager with clash detection, and animated goal completion. Data persisted locally via SQLite with a clean data-access abstraction layer.
