"""
review.py -- Weekly and Monthly Review module for Lakshya.
Standalone Click group (review_group).  No imports from db.py or lakshya.py.
ASCII-only output -- safe for Windows cp1252 terminals.
"""

import os
import sqlite3
import click
import re
from datetime import date, timedelta
from collections import defaultdict

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align
from rich import print as rprint

DB_FILE = os.path.join(os.path.expanduser("~"), ".lakshya", "goals.db")
console = Console()
TYPE_COLORS = {"daily": "green", "weekly": "cyan", "monthly": "yellow", "yearly": "red"}


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_conn():
    if not os.path.exists(DB_FILE):
        console.print("[bold red]DB not found. Run lakshya once to initialise.[/bold red]")
        raise SystemExit(1)
    return sqlite3.connect(DB_FILE)


def _get_completions_range(start_iso, end_iso):
    conn = _get_conn()
    c = conn.cursor()
    c.execute(
        """SELECT c.completed_on, g.title, g.type
           FROM completions c JOIN goals g ON c.goal_id = g.id
           WHERE c.completed_on BETWEEN ? AND ?
           ORDER BY c.completed_on ASC, g.title ASC""",
        (start_iso, end_iso),
    )
    rows = c.fetchall()
    conn.close()
    return [{"completed_on": r[0], "title": r[1], "type": r[2]} for r in rows]


def _get_daily_goals():
    conn = _get_conn()
    c = conn.cursor()
    c.execute("SELECT id, title, type FROM goals WHERE type='daily' ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "title": r[1], "type": r[2]} for r in rows]


def _calc_streak(goal_id):
    conn = _get_conn()
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
    first = date.fromisoformat(rows[0][0])
    if first != today and first != today - timedelta(days=1):
        return 0
    streak = 0
    check = first
    for row in rows:
        d = date.fromisoformat(row[0])
        if d == check:
            streak += 1
            check -= timedelta(days=1)
        else:
            break
    return streak


def _heatmap_cell(count):
    if count == 0:   return "."
    elif count == 1: return "[green]o[/green]"
    elif count <= 3: return "[bold green]*[/bold green]"
    else:            return "[bold blue]#[/bold blue]"


def _plain_cell(count):
    if count == 0:   return "."
    elif count == 1: return "o"
    elif count <= 3: return "*"
    else:            return "#"


def _by_day(rows):
    d = defaultdict(int)
    for r in rows:
        d[r["completed_on"]] += 1
    return d


def _best_day(by_day):
    if not by_day:
        return None, 0
    best = max(by_day, key=lambda k: by_day[k])
    return best, by_day[best]


def _write_report(lines, filename):
    strip = re.compile(r"\[/?[^\[\]]*\]")
    with open(filename, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(strip.sub("", line) + "\n")


# ── Click group ────────────────────────────────────────────────────────────────

@click.group("review")
def review_group():
    """Generate weekly and monthly review reports."""
    pass


# ── review weekly ──────────────────────────────────────────────────────────────

@review_group.command("weekly")
def review_weekly():
    """Full 7-day review: completions, streaks, heatmap, best day."""
    today      = date.today()
    week_end   = today
    week_start = today - timedelta(days=6)
    rows   = _get_completions_range(week_start.isoformat(), week_end.isoformat())
    by_day = _by_day(rows)

    header = ("Weekly Review -- "
               + week_start.strftime("%a %d %b")
               + "  to  "
               + week_end.strftime("%a %d %b %Y"))
    console.print()
    console.print(Panel(Align.center(f"[bold white]{header}[/bold white]"),
                        border_style="bold cyan", expand=False))
    pl = ["=" * 60, header, "=" * 60]

    # Goals completed table
    console.print("\n[bold yellow]Goals Completed This Week[/bold yellow]")
    pl += ["\nGoals Completed This Week", "-" * 40]
    if not rows:
        rprint("[dim]  No completions this period.[/dim]")
        pl.append("  No completions this period.")
    else:
        t = Table(show_header=True, header_style="bold magenta", border_style="magenta")
        t.add_column("Day",  style="cyan",    no_wrap=True)
        t.add_column("Type", style="magenta", no_wrap=True)
        t.add_column("Goal", style="white")
        for r in rows:
            d   = date.fromisoformat(r["completed_on"])
            ds  = d.strftime("%a %d %b")
            col = TYPE_COLORS.get(r["type"], "white")
            t.add_row(ds, f"[{col}]{r['type']}[/{col}]", r["title"])
            pl.append(f"  {ds:<14}  {r['type']:<9}  {r['title']}")
        console.print(t)

    # Streak summary
    console.print("\n[bold yellow]Streak Summary -- Daily Goals[/bold yellow]")
    pl += ["\nStreak Summary -- Daily Goals", "-" * 40]
    dg = _get_daily_goals()
    if not dg:
        rprint("[dim]  No daily goals.[/dim]")
        pl.append("  No daily goals.")
    else:
        st = Table(show_header=True, header_style="bold green", border_style="green")
        st.add_column("Goal",   style="white")
        st.add_column("Streak", justify="center")
        for g in dg:
            s  = _calc_streak(g["id"])
            ss = f"{s} day(s)" if s > 0 else "0"
            c  = "bold green" if s >= 7 else "green" if s >= 3 else "yellow" if s >= 1 else "dim"
            st.add_row(g["title"], f"[{c}]{ss}[/{c}]")
            pl.append(f"  {g['title']:<35}  {ss}")
        console.print(st)

    # 7-day heatmap
    console.print("\n[bold yellow]7-Day Heatmap[/bold yellow]")
    pl += ["\n7-Day Heatmap", "-" * 40]
    hcells, hlabels, pcells = [], [], []
    for i in range(7):
        d   = week_start + timedelta(days=i)
        cnt = by_day.get(d.isoformat(), 0)
        hcells.append(_heatmap_cell(cnt))
        hlabels.append(d.strftime("%d"))
        pcells.append(_plain_cell(cnt))
    legend = ("[dim]. = none   [green]o[/green] = 1   "
              "[bold green]*[/bold green] = 2-3   "
              "[bold blue]#[/bold blue] = 4+[/dim]")
    console.print(Panel(
        "  ".join(hcells) + "\n[dim]" + "  ".join(hlabels) + "[/dim]\n\n" + legend,
        border_style="cyan", expand=False))
    pl.append("  " + "  ".join(pcells))
    pl.append("  " + "  ".join(hlabels))
    pl.append("  . = none  o = 1  * = 2-3  # = 4+")

    # Best day
    best_iso, best_cnt = _best_day(by_day)
    console.print("\n[bold yellow]Best Day This Week[/bold yellow]")
    pl += ["\nBest Day This Week", "-" * 40]
    if best_iso:
        bds = date.fromisoformat(best_iso).strftime("%A, %d %b %Y")
        console.print(f"  [bold green]{bds}[/bold green]  --  [bold white]{best_cnt}[/bold white] completion(s)")
        pl.append(f"  {bds}  --  {best_cnt} completion(s)")
    else:
        rprint("[dim]  No activity this week.[/dim]")
        pl.append("  No activity this week.")

    # Motivational closing
    total = sum(by_day.values())
    if total >= 20:   msg = "BEAST MODE.  Nothing can stop you."
    elif total >= 10: msg = "Solid week.  Keep the momentum going!"
    elif total >= 5:  msg = "Good progress.  Push harder next week."
    elif total >= 1:  msg = "You showed up.  That counts.  Build on it."
    else:             msg = "Every champion has a slow week.  Come back stronger."

    console.print()
    console.print(Panel(
        f"[bold white]{msg}[/bold white]\n\n"
        f"[dim]Total completions this week: {total}[/dim]",
        title="[bold green] Keep Going! [/bold green]",
        border_style="green", expand=False))
    pl += ["\n" + "=" * 60, msg, f"Total completions this week: {total}", "=" * 60]

    # Export prompt
    console.print()
    save = console.input("[bold cyan]Save report to file? (y/n): [/bold cyan]").strip().lower()
    if save in ("y", "yes"):
        fn = f"weekly_review_{today.isoformat()}.txt"
        _write_report(pl, fn)
        rprint(f"[bold green]Saved to {fn}[/bold green]")
    else:
        rprint("[dim]Report not saved.[/dim]")


# ── review monthly ─────────────────────────────────────────────────────────────

@review_group.command("monthly")
def review_monthly():
    """Calendar-month review: completions by type, top goals, gaps, rate."""
    today       = date.today()
    month_start = today.replace(day=1)
    month_end   = today
    rows   = _get_completions_range(month_start.isoformat(), month_end.isoformat())
    by_day = _by_day(rows)
    ml     = today.strftime("%B %Y")

    console.print()
    console.print(Panel(Align.center(f"[bold white]Monthly Review -- {ml}[/bold white]"),
                        border_style="bold yellow", expand=False))
    pl = ["=" * 60, f"Monthly Review -- {ml}", "=" * 60]

    # Completions by type
    console.print("\n[bold yellow]Completions by Goal Type[/bold yellow]")
    pl += ["\nCompletions by Goal Type", "-" * 40]
    tc = defaultdict(int)
    for r in rows:
        tc[r["type"]] += 1
    tt = Table(show_header=True, header_style="bold magenta", border_style="magenta")
    tt.add_column("Type",        style="magenta")
    tt.add_column("Completions", justify="right")
    for gt in ("daily", "weekly", "monthly", "yearly"):
        cnt = tc.get(gt, 0)
        col = TYPE_COLORS.get(gt, "white")
        tt.add_row(f"[{col}]{gt}[/{col}]", f"[bold {col}]{cnt}[/bold {col}]")
        pl.append(f"  {gt:<12}  {cnt}")
    console.print(tt)

    # Top 3 most-completed goals
    console.print("\n[bold yellow]Top 3 Most-Completed Goals This Month[/bold yellow]")
    pl += ["\nTop 3 Most-Completed Goals This Month", "-" * 40]
    gc = defaultdict(lambda: {"count": 0, "type": ""})
    for r in rows:
        gc[r["title"]]["count"] += 1
        gc[r["title"]]["type"]   = r["type"]
    top3 = sorted(gc.items(), key=lambda x: x[1]["count"], reverse=True)[:3]
    if not top3:
        rprint("[dim]  No completions this month.[/dim]")
        pl.append("  No completions this month.")
    else:
        rt = Table(show_header=True, header_style="bold cyan", border_style="cyan")
        rt.add_column("Rank",      justify="center", style="bold yellow")
        rt.add_column("Goal",      style="white")
        rt.add_column("Type",      style="magenta")
        rt.add_column("Days Done", justify="right",  style="bold green")
        for i, (title, info) in enumerate(top3):
            col = TYPE_COLORS.get(info["type"], "white")
            rt.add_row(f"{i+1}.", title, f"[{col}]{info['type']}[/{col}]", str(info["count"]))
            pl.append(f"  {i+1}.  {title:<30}  {info['type']:<9}  {info['count']} day(s)")
        console.print(rt)

    # Gap days
    console.print("\n[bold yellow]Days with Zero Activity (Gaps)[/bold yellow]")
    pl += ["\nDays with Zero Activity (Gaps)", "-" * 40]
    total_days = (month_end - month_start).days + 1
    gap_days = [month_start + timedelta(days=i)
                for i in range(total_days)
                if (month_start + timedelta(days=i)).isoformat() not in by_day]
    if not gap_days:
        rprint("[bold green]  No gaps -- every day had at least one completion![/bold green]")
        pl.append("  No gaps!")
    else:
        groups, gs, ge = [], gap_days[0], gap_days[0]
        for d in gap_days[1:]:
            if (d - ge).days == 1:
                ge = d
            else:
                groups.append((gs, ge)); gs = d; ge = d
        groups.append((gs, ge))
        gt2 = Table(show_header=True, header_style="bold red", border_style="red")
        gt2.add_column("Gap Period",  style="red")
        gt2.add_column("Days Missed", justify="right", style="bold red")
        for gs2, ge2 in groups:
            period = gs2.strftime("%d %b") if gs2 == ge2 else gs2.strftime("%d %b") + " - " + ge2.strftime("%d %b")
            missed = 1 if gs2 == ge2 else (ge2 - gs2).days + 1
            gt2.add_row(period, str(missed))
            pl.append(f"  {period:<25}  {missed} day(s)")
        console.print(gt2)

    # Completion rate
    console.print("\n[bold yellow]Completion Rate[/bold yellow]")
    pl += ["\nCompletion Rate", "-" * 40]
    active = total_days - len(gap_days)
    rate   = (active / total_days * 100) if total_days > 0 else 0.0
    filled = int(rate / 5)
    bar    = "=" * filled + "-" * (20 - filled)
    rc     = "bold green" if rate >= 80 else "yellow" if rate >= 50 else "red"
    console.print(f"  [{rc}][{bar}][/{rc}]  [bold white]{active}[/bold white] / {total_days} days  [{rc}]({rate:.1f}%)[/{rc}]")
    pl.append(f"  [{bar}]  {active} / {total_days} days  ({rate:.1f}%)")

    console.print()
    console.print(Panel(
        f"[bold white]Month              : {ml}[/bold white]\n"
        f"Total completions  : [bold cyan]{len(rows)}[/bold cyan]\n"
        f"Active days        : [bold green]{active}[/bold green] / {total_days}\n"
        f"Overall rate       : [{rc}]{rate:.1f}%[/{rc}]",
        title="[bold yellow] Monthly Summary [/bold yellow]",
        border_style="yellow", expand=False))

    console.print()
    save = console.input("[bold cyan]Save report to file? (y/n): [/bold cyan]").strip().lower()
    if save in ("y", "yes"):
        fn = f"monthly_review_{today.strftime('%Y-%m')}.txt"
        _write_report(pl, fn)
        rprint(f"[bold green]Saved to {fn}[/bold green]")
    else:
        rprint("[dim]Report not saved.[/dim]")
