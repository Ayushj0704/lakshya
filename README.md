# Lakshya (लक्ष्य) — The Minimalist Goal Engine

> *lak·shya* — Sanskrit for **target, aim, goal**

Lakshya is a fast, keyboard-first, terminal-based productivity engine built in Python.
No internet. No subscriptions. No distractions. Just you and your goals.

<!-- Add your screenshots in an 'assets' folder and uncomment this: 
![CLI Dashboard](assets/cli-screenshot.png) 
-->

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
| **Finance Tracker** | Track income, expenses, budgets, and link savings to goals |
| **Windows Reminders** | Schedule Task Scheduler popup reminders (no daemon needed) |
| **Weekly Review** | Auto-generate beautiful terminal reports of your week |
| **Full Web Dashboard**| Start the included FastAPI server for a web UI view |
| **Export** | Export all goals to CSV or Markdown |
| **Local SQLite Storage** | All data stored in `~/.lakshya/goals.db` — 100% private |

---

## Installation

### 1. Clone the repository
```powershell
git clone https://github.com/Ayushj0704/lakshya.git
cd lakshya
```

### 2. Run the one-click installer
This will create a Python virtual environment, install all dependencies, and register the global command.
```powershell
.\install.bat
```

### 3. Activate the environment & Run
You must activate the virtual environment before running the tool for the first time in a new terminal session.
```powershell
# Activate the venv
.\venv\Scripts\Activate.ps1

# Launch the interactive shell!
lakshya
```

> **Tip:** After the venv is activated, you can type `lakshya` from any folder on your computer.
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

## Finance Tracker

Track income, expenses, budgets, and link savings to your main goals.

```bash
lakshya> finance add       # Add an expense or income
lakshya> finance ls        # View all transactions this month
lakshya> finance budget    # Set a monthly limit for a category (e.g. food)
lakshya> finance summary   # Rich visual breakdown of budget usage
lakshya> finance goal      # Create a linked savings goal
lakshya> finance rm 1      # Delete transaction #1
```

---

## Windows Reminders

Schedule recurring desktop notifications using Windows Task Scheduler (no background process needed).

```bash
lakshya> remind add        # Schedule a new toast notification
lakshya> remind ls         # List active scheduled tasks
lakshya> remind rm 1       # Delete a reminder
lakshya> remind test       # Fire a test notification immediately
```

---

## Weekly & Monthly Reviews

Auto-generate beautiful terminal reports summarizing your progress.

```bash
lakshya> review weekly     # 7-day heatmap, streak summary, best day
lakshya> review monthly    # 30-day top goals, gap days, completion rate
```
*(Both commands let you save the output to a text file.)*

---

## Web Dashboard (FastAPI)

Lakshya includes a complete REST API and vanilla JS web dashboard.

```bash
# From the project root:
cd web
.\run.bat
```
Then open `http://localhost:8000` in your browser to see your goals, streaks, and heatmap on the web!

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
├── finance_db.py     # SQLite layer for Finance Tracker
├── reminders_db.py   # Windows Task Scheduler integration
├── web/              # FastAPI Web Dashboard 
├── setup.py          # Package config for global `lakshya` command
├── install.bat       # One-click installer
├── lakshya.bat       # Quick runner (no global install needed)
└── README.md         # This file
```

Data is stored at: `~/.lakshya/goals.db` (usually `C:\Users\<you>\.lakshya\goals.db`)

---

## Tech Stack

- **Python 3.8+**
- **[FastAPI](https://fastapi.tiangolo.com/)** — Web API backend
- **[Click](https://click.palletsprojects.com/)** — CLI framework
- **[Rich](https://github.com/Textar/rich)** — Terminal UI (tables, panels, spinners, progress bars)
- **SQLite** — local database, zero config

---

## Motivation

> "Most goal apps are designed for people who want to feel productive. Lakshya is built for people who want to **be** productive."

I built Lakshya because existing tools require subscriptions, don't work offline, or have too much clutter. By moving goal management to the terminal, it becomes a frictionless part of a developer's existing workflow — no browser tabs, no ads, no accounts.
