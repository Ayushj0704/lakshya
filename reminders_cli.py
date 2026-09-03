"""
reminders_cli.py -- CLI layer for the Lakshya Reminders module.
Commands: remind add | remind ls | remind rm | remind test
"""

import os
import re
import subprocess

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

import reminders_db

reminders_db.init_reminders_db()

console = Console()

_DAYS_MAP = {
    "weekdays": "0,1,2,3,4",
    "weekends": "5,6",
    "daily":    "0,1,2,3,4,5,6",
}

_DAY_NAMES = {"0": "Mon", "1": "Tue", "2": "Wed", "3": "Thu", "4": "Fri", "5": "Sat", "6": "Sun"}


def _days_label(days_str):
    return " ".join(_DAY_NAMES.get(d.strip(), d.strip()) for d in days_str.split(","))


def _make_task_name(reminder_id, label):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", label)[:30]
    return "Lakshya_Reminder_{}_{}".format(reminder_id, safe)


def _venv_python():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv", "Scripts", "python.exe")


def _notify_script():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "remind_notify.py")


def _validate_time(time_str):
    return bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", time_str))


@click.group("remind")
def reminders_group():
    """Reminders -- schedule recurring alerts via Windows Task Scheduler."""


@reminders_group.command("add")
@click.option("--label",       "-l", default=None)
@click.option("--time",        "-t", default=None, help="HH:MM (24h)")
@click.option("--days",        "-d", default=None,
              type=click.Choice(["weekdays", "weekends", "daily", "custom"], case_sensitive=False))
@click.option("--custom-days", default=None, help="Comma-separated 0-6 when --days=custom")
@click.option("--goal-id",     "-g", default=None, type=int)
def remind_add(label, time, days, custom_days, goal_id):
    """Schedule a new recurring reminder."""
    if not label:
        label = click.prompt("Reminder label")
    label = label.strip()
    if not label:
        console.print(Panel("[red]Label cannot be empty.[/red]", title="Error")); return

    if not time:
        time = click.prompt("Time (HH:MM, 24-hour)")
    if not _validate_time(time):
        console.print(Panel("[red]Invalid time '{}'. Use HH:MM.[/red]".format(time), title="Error")); return

    if not days:
        days = click.prompt("Days", type=click.Choice(["weekdays","weekends","daily","custom"], case_sensitive=False), default="daily")

    if days == "custom":
        if not custom_days:
            custom_days = click.prompt("Day numbers 0-6 comma-separated (0=Mon)")
        days_str = custom_days.strip()
        for part in days_str.split(","):
            if part.strip() not in {"0","1","2","3","4","5","6"}:
                console.print(Panel("[red]Invalid day '{}'.[/red]".format(part.strip()), title="Error")); return
    else:
        days_str = _DAYS_MAP[days]

    rid       = reminders_db.add_reminder(label, time, days_str, goal_id=goal_id)
    task_name = _make_task_name(rid, label)
    ok        = reminders_db.schedule_windows_task(task_name, time, _notify_script(), _venv_python(), label)

    if ok:
        reminders_db.update_task_name(rid, task_name)
        console.print(Panel(
            "[green]Reminder #{} scheduled![/green]\n  Label : {}\n  Time  : {}\n  Days  : {}\n  Task  : {}".format(
                rid, label, time, _days_label(days_str), task_name),
            title="[bold green]Reminder Added[/bold green]"
        ))
    else:
        console.print(Panel(
            "[yellow]Saved to DB but Task Scheduler registration failed.\n"
            "Manual command:\n  schtasks /create /tn {} /tr \"{} {} {}\" /sc DAILY /st {} /f[/yellow]".format(
                task_name, _venv_python(), _notify_script(), label, time),
            title="[bold yellow]Partial Success[/bold yellow]"
        ))


@reminders_group.command("ls")
def remind_ls():
    """List all active reminders."""
    rows = reminders_db.get_reminders()
    if not rows:
        console.print(Panel("[dim]No active reminders.[/dim]", title="Reminders")); return

    tbl = Table(title="Active Reminders", show_lines=True)
    tbl.add_column("ID",    style="bold cyan",  no_wrap=True)
    tbl.add_column("Label", style="bold white")
    tbl.add_column("Time",  style="green",  no_wrap=True)
    tbl.add_column("Days",  style="yellow")
    tbl.add_column("Goal",  style="magenta", no_wrap=True)
    tbl.add_column("Task Name", style="dim")

    for r in rows:
        tbl.add_row(
            str(r["id"]), r["label"], r["remind_at"],
            _days_label(r["days"]),
            str(r["goal_id"]) if r["goal_id"] else "-",
            r["task_name"] or "-",
        )
    console.print(tbl)


@reminders_group.command("rm")
@click.argument("reminder_id", type=int)
def remind_rm(reminder_id):
    """Delete a reminder and unschedule its Windows task."""
    reminder = reminders_db.get_reminder_by_id(reminder_id)
    if not reminder:
        console.print(Panel("[red]No active reminder with ID {}.[/red]".format(reminder_id), title="Error")); return

    ok = reminders_db.delete_reminder(reminder_id)
    if ok:
        console.print(Panel("[green]Reminder #{} deleted and unscheduled.[/green]".format(reminder_id),
                            title="[bold green]Removed[/bold green]"))
    else:
        console.print(Panel(
            "[yellow]Deleted from DB but could not unschedule task '{}'.\n"
            "Manual: schtasks /delete /tn {} /f[/yellow]".format(reminder.get("task_name",""), reminder.get("task_name","")),
            title="[bold yellow]Partial Removal[/bold yellow]"
        ))


@reminders_group.command("test")
@click.option("--message", "-m", default="This is a Lakshya test reminder!")
def remind_test(message):
    """Fire a test notification immediately."""
    console.print("[dim]Firing test notification...[/dim]")
    try:
        result = subprocess.run([_venv_python(), _notify_script(), message], timeout=20)
        if result.returncode == 0:
            console.print(Panel("[green]Test notification sent![/green]", title="[bold green]Test OK[/bold green]"))
        else:
            console.print(Panel("[yellow]remind_notify.py exited with code {}.[/yellow]".format(result.returncode), title="Warning"))
    except subprocess.TimeoutExpired:
        console.print(Panel("[red]Test timed out.[/red]", title="Error"))
    except FileNotFoundError:
        console.print(Panel("[red]Python not found at venv path. Check venv setup.[/red]", title="Error"))
    except Exception as exc:
        console.print(Panel("[red]Error: {}[/red]".format(exc), title="Error"))
