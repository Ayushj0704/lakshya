import click
import difflib
import shlex
import time
from datetime import date, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from rich import print as rprint
from rich.panel import Panel
from rich.align import Align
from rich.text import Text
from rich.prompt import Prompt
from rich.live import Live
import db

console = Console()

# ── Splash Screen ─────────────────────────────────────────────────────────────

def show_splash():
    lines = [
        "  _          _        _                      ",
        " | |    __ _| | _____| |__  _   _  __ _     ",
        " | |   / _` | |/ / __| '_ \\| | | |/ _` |   ",
        " | |__| (_| |   <\\__ \\ | | | |_| | (_| |   ",
        " |_____\\__,_|_|\\_\\___/_| |_|\\__, |\\__,_|   ",
        "                             |___/           ",
    ]
    colors = ["bold red", "bold yellow", "bold green", "bold cyan", "bold blue", "bold magenta"]
    console.clear()
    for i, line in enumerate(lines):
        console.print(Align.center(f"[{colors[i]}]{line}[/]"))
        time.sleep(0.08)

    console.print(Align.center("\n[bold white on dark_magenta]  THE MINIMALIST GOAL ENGINE  [/bold white on dark_magenta]\n"))
    console.print(Align.center("[dim]lak·shya (लक्ष्य) — Sanskrit: target, aim, goal[/dim]\n"))
    time.sleep(0.3)

# ── Fuzzy Command Matching ────────────────────────────────────────────────────

class FuzzyGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = difflib.get_close_matches(cmd_name, self.list_commands(ctx), n=1, cutoff=0.5)
        if matches:
            console.print(f"[yellow]Tip: Did you mean '[bold]{matches[0]}[/bold]'?[/yellow]")
        return None

# ── CLI Root ──────────────────────────────────────────────────────────────────

@click.group(cls=FuzzyGroup, invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Lakshya — Your personal goal engine."""
    db.init_db()
    if ctx.invoked_subcommand is None:
        show_splash()
        interactive_mode()


def interactive_mode():
    rprint("[dim]Type '[bold]help[/bold]' for all commands, '[bold]exit[/bold]' to quit.[/dim]\n")
    while True:
        try:
            raw = Prompt.ask("[bold cyan]lakshya[/bold cyan][bold white]>[/bold white]")
            if not raw.strip():
                continue
            cmd_lower = raw.strip().lower()

            if cmd_lower in ("exit", "quit", "q"):
                rprint("[green]Goodbye! Keep chasing your Lakshya![/green]")
                break

            if cmd_lower == "help":
                with click.Context(cli) as ctx:
                    click.echo(cli.get_help(ctx))
                continue

            try:
                args = shlex.split(raw)
            except ValueError as e:
                rprint(f"[red]Parse error: {e}[/red]")
                continue

            try:
                cli.main(args=args, standalone_mode=False)
            except click.UsageError as e:
                rprint(f"[red]Usage error: {e}[/red]")
            except (click.exceptions.Exit, SystemExit):
                pass
            except Exception as e:
                rprint(f"[red]Error: {e}[/red]")

        except KeyboardInterrupt:
            rprint("\n[green]Goodbye! Keep chasing your Lakshya![/green]")
            break
        except EOFError:
            break

# ── Dancing Cat ───────────────────────────────────────────────────────────────

def dancing_cat():
    frames = [
        "[bold magenta] /\\_/\\  [/]\n[bold magenta]( o.o ) [/]\n[bold yellow] > ^ <  GOAL SMASHED![/]",
        "[bold cyan] /\\_/\\  [/]\n[bold cyan]( -.- ) [/]\n[bold yellow]  > ^ < AMAZING!!![/]",
        "[bold green] /\\_/\\  [/]\n[bold green]( ^.^ ) [/]\n[bold yellow]< ^ >   YOU ROCK![/]",
        "[bold red] /\\_/\\  [/]\n[bold red]( o.O ) [/]\n[bold yellow] > ^ <  LAKSHYA![/]",
    ]
    with Live(refresh_per_second=8, transient=True) as live:
        for _ in range(10):
            for frame in frames:
                live.update(Align.center(Panel(frame, border_style="bold yellow", expand=False)))
                time.sleep(0.2)

# ── GOALS Commands ────────────────────────────────────────────────────────────

@cli.command()
@click.argument("title", required=False)
@click.option("--desc", "-d", default="", help="Description")
@click.option("--type", "-t", "goal_type",
              type=click.Choice(["daily", "weekly", "monthly", "yearly"]),
              help="Type of goal")
def add(title, desc, goal_type):
    """Add a new goal (interactive prompts if args missing)."""
    if not title:
        title = Prompt.ask("[bold yellow]Goal title?[/bold yellow]")
    if not goal_type:
        goal_type = Prompt.ask(
            "[bold yellow]Type?[/bold yellow]",
            choices=["daily", "weekly", "monthly", "yearly"],
            default="daily"
        )
    if not desc:
        desc = Prompt.ask("[bold yellow]Description (optional)[/bold yellow]", default="")

    type_colors = {"daily": "green", "weekly": "cyan", "monthly": "yellow", "yearly": "red"}
    color = type_colors.get(goal_type, "white")

    with Progress(SpinnerColumn("dots"), TextColumn(f"[{color}]Forging your Lakshya..."), transient=True) as p:
        p.add_task("", total=None)
        time.sleep(0.8)
        goal_id = db.add_goal(title, desc, goal_type)

    console.print(Panel(
        f"[bold white]{title}[/bold white]\n[dim]{desc}[/dim]",
        title=f"[bold {color}] {goal_type.upper()} Goal #{goal_id} created! [/bold {color}]",
        border_style=color,
        expand=False
    ))


@cli.command("day")
def create_day():
    """Quick-add a daily habit/task."""
    title = Prompt.ask("[bold yellow]Daily task?[/bold yellow]")
    desc  = Prompt.ask("[bold yellow]Description (optional)[/bold yellow]", default="")
    with console.status("[bold green]Saving daily task...", spinner="dots"):
        time.sleep(0.4)
        gid = db.add_goal(title, desc, "daily")
    console.print(Panel(f"[bold white]{title}[/bold white]", title=f"[bold green] DAILY task #{gid} saved! [/bold green]", expand=False))


@cli.command("week")
def create_week():
    """Quick-add a weekly goal."""
    title = Prompt.ask("[bold yellow]Weekly goal?[/bold yellow]")
    desc  = Prompt.ask("[bold yellow]Description (optional)[/bold yellow]", default="")
    with console.status("[bold cyan]Saving weekly goal...", spinner="dots"):
        time.sleep(0.4)
        gid = db.add_goal(title, desc, "weekly")
    console.print(Panel(f"[bold white]{title}[/bold white]", title=f"[bold cyan] WEEKLY goal #{gid} saved! [/bold cyan]", expand=False))


@cli.command("month")
def create_month():
    """Quick-add a monthly goal."""
    title = Prompt.ask("[bold yellow]Monthly goal?[/bold yellow]")
    desc  = Prompt.ask("[bold yellow]Description (optional)[/bold yellow]", default="")
    with console.status("[bold yellow]Saving monthly goal...", spinner="dots"):
        time.sleep(0.4)
        gid = db.add_goal(title, desc, "monthly")
    console.print(Panel(f"[bold white]{title}[/bold white]", title=f"[bold yellow] MONTHLY goal #{gid} saved! [/bold yellow]", expand=False))


@cli.command("year")
def create_year():
    """Quick-add a yearly goal."""
    title = Prompt.ask("[bold yellow]Yearly goal?[/bold yellow]")
    desc  = Prompt.ask("[bold yellow]Description (optional)[/bold yellow]", default="")
    with console.status("[bold red]Saving yearly goal...", spinner="dots"):
        time.sleep(0.4)
        gid = db.add_goal(title, desc, "yearly")
    console.print(Panel(f"[bold white]{title}[/bold white]", title=f"[bold red] YEARLY goal #{gid} saved! [/bold red]", expand=False))


@cli.command("ls")
@click.option("--type", "-t", "goal_type",
              type=click.Choice(["daily", "weekly", "monthly", "yearly", "all"]), default="all")
@click.option("--status", "-s", type=click.Choice(["pending", "completed", "all"]), default="all")
def ls(goal_type, status):
    """List your goals."""
    goals = db.get_goals(
        None if goal_type == "all" else goal_type,
        None if status == "all" else status
    )
    if not goals:
        rprint("[yellow]No goals found.[/yellow]")
        return

    type_colors = {"daily": "green", "weekly": "cyan", "monthly": "yellow", "yearly": "red"}

    table = Table(title="Your Lakshyas", show_header=True, header_style="bold magenta", border_style="magenta")
    table.add_column("ID",      justify="right", style="cyan",    no_wrap=True)
    table.add_column("Type",    style="magenta", no_wrap=True)
    table.add_column("Title",   style="white")
    table.add_column("Status",  no_wrap=True)
    table.add_column("Progress / Streak", style="blue")

    for g in goals:
        color = type_colors.get(g["type"], "white")
        status_str = "[bold green][v][/bold green]" if g["status"] == "completed" else "[yellow][ ][/yellow]"

        extra = ""
        if g["type"] in ("yearly", "monthly"):
            prog   = g["progress"]
            filled = int(prog / 10)
            bar    = "=" * filled + "-" * (10 - filled)
            extra  = f"[{color}][{bar}][/{color}] {prog}%"
        elif g["type"] in ("daily", "weekly"):
            streak = db.get_streak(g["id"])
            if streak > 0:
                extra = f"[bold {color}]{streak} day streak![/bold {color}]"

        table.add_row(str(g["id"]), f"[{color}]{g['type']}[/{color}]", g["title"], status_str, extra)

    console.print(table)


@cli.command("done")
@click.argument("goal_id", type=int)
def done(goal_id):
    """Mark a goal as completed — with a celebration!"""
    with Progress(SpinnerColumn("bouncingBall"), TextColumn("[bold cyan]Submitting victory..."), transient=True) as p:
        p.add_task("", total=None)
        time.sleep(0.8)
        success = db.update_goal_status(goal_id, "completed")

    if success:
        dancing_cat()
        console.print(Align.center(f"\n[bold green reverse]  *** GOAL #{goal_id} CONQUERED — LAKSHYA ACHIEVED! ***  [/bold green reverse]\n"))
    else:
        rprint(f"[red]Goal #{goal_id} not found.[/red]")


@cli.command("undo")
@click.argument("goal_id", type=int)
def undo(goal_id):
    """Revert a goal back to pending."""
    if db.update_goal_status(goal_id, "pending"):
        rprint(f"[yellow]Goal #{goal_id} marked as pending again.[/yellow]")
    else:
        rprint(f"[red]Goal #{goal_id} not found.[/red]")


@cli.command("progress")
@click.argument("goal_id", type=int)
@click.argument("percent", type=click.IntRange(0, 100))
def progress(goal_id, percent):
    """Update the % progress of a monthly/yearly goal."""
    if db.update_progress(goal_id, percent):
        filled = int(percent / 10)
        bar = "=" * filled + "-" * (10 - filled)
        rprint(f"[blue]Goal #{goal_id}  [{bar}] {percent}%[/blue]")
    else:
        rprint(f"[red]Goal #{goal_id} not found.[/red]")


@cli.command("rm")
@click.argument("goal_id", type=int)
def rm(goal_id):
    """Delete a goal."""
    if db.delete_goal(goal_id):
        rprint(f"[green]Goal #{goal_id} deleted.[/green]")
    else:
        rprint(f"[red]Goal #{goal_id} not found.[/red]")


# ── Heatmap ───────────────────────────────────────────────────────────────────

@cli.command("heatmap")
@click.option("--period", "-p", default="", help="month/year (m or y shorthand works too)")
def heatmap(period):
    """Show an activity heatmap."""
    # Normalise shorthand: y → year, m → month
    if period.lower() in ("y", "yr", "year"):
        period = "year"
    elif period.lower() in ("m", "mo", "month"):
        period = "month"
    else:
        raw = Prompt.ask(
            "[bold yellow]Period? (m)onth or (y)ear[/bold yellow]",
            default="m"
        )
        period = "year" if raw.lower().startswith("y") else "month"

    days_to_show = 30 if period == "month" else 365
    data = db.get_heatmap_data(days_to_show)
    today = date.today()
    days = [today - timedelta(days=i) for i in range(days_to_show - 1, -1, -1)]

    cols = 7 if period == "month" else 30
    # Build legend + date header
    if period == "month":
        # Show weekday headers
        header = " ".join(f"[dim]{d[:2]}[/dim]" for d in ["Mo","Tu","We","Th","Fr","Sa","Su"])
        rprint(f"\n[bold cyan]Activity Heatmap — {today.strftime('%B %Y')}[/bold cyan]")
        console.print(Align.left(header, pad=False))
    else:
        rprint(f"\n[bold cyan]Activity Heatmap — {today.strftime('%Y')} (last 365 days)[/bold cyan]")

    # Build grid rows
    grid_lines = []
    row = ""
    for i, d in enumerate(days):
        c = data.get(d.isoformat(), 0)
        if c == 0:
            cell = ". "
        elif c == 1:
            cell = "[green]o [/green]"
        elif c <= 3:
            cell = "[bold green]* [/bold green]"
        else:
            cell = "[bold blue]# [/bold blue]"
        row += cell
        if (i + 1) % cols == 0:
            grid_lines.append(row.rstrip())
            row = ""
    if row:
        grid_lines.append(row.rstrip())

    legend = "\n[dim]. = none   [green]o[/green] = 1   [bold green]*[/bold green] = 2-3   [bold blue]#[/bold blue] = 4+[/dim]"
    grid_text = "\n".join(grid_lines)

    first_day = days[0].strftime("%d %b %Y")
    last_day  = days[-1].strftime("%d %b %Y")
    console.print(Panel(
        f"{grid_text}\n{legend}",
        title=f"[bold]{first_day}  to  {last_day}[/bold]",
        border_style="cyan",
        expand=False
    ))


# ── Focus Clock ───────────────────────────────────────────────────────────────

@cli.command("clock")
@click.option("--minutes", "-m", default=0.0, type=float, help="Duration in minutes (supports decimals)")
def clock(minutes):
    """Start a Pomodoro-style focus timer."""
    if minutes <= 0:
        raw = Prompt.ask("[bold yellow]How many minutes?[/bold yellow]", default="25")
        try:
            minutes = float(raw)
        except ValueError:
            minutes = 25.0

    seconds = max(1, int(minutes * 60))
    label = f"{minutes:.4g} min"
    rprint(f"[bold cyan]Starting {label} focus session... Stay locked in![/bold cyan]\n")

    with Progress(
        SpinnerColumn("dots"),
        TextColumn("[bold green]Focusing..."),
        BarColumn(bar_width=40),
        TimeRemainingColumn(),
        console=console
    ) as bar:
        task = bar.add_task("", total=seconds)
        while not bar.finished:
            time.sleep(1)
            bar.update(task, advance=1)

    console.print(Align.center("\n[bold green reverse]  FOCUS SESSION COMPLETE - Take a deserved break!  [/bold green reverse]\n"))


# ── Timetable ─────────────────────────────────────────────────────────────────

DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

@cli.group("tt")
def timetable():
    """Manage your college/work timetable."""
    pass


@timetable.command("add")
def tt_add():
    """Add a class/slot to your timetable."""
    rprint("[bold cyan]Days: 0=Mon  1=Tue  2=Wed  3=Thu  4=Fri  5=Sat  6=Sun[/bold cyan]")
    day_str = Prompt.ask("[bold yellow]Day number (0-6)[/bold yellow]")
    try:
        day = int(day_str)
        if day < 0 or day > 6:
            raise ValueError
    except ValueError:
        rprint("[red]Invalid day. Use 0–6.[/red]")
        return

    start = Prompt.ask("[bold yellow]Start time (HH:MM, 24h)[/bold yellow]")
    end   = Prompt.ask("[bold yellow]End time   (HH:MM, 24h)[/bold yellow]")
    label = Prompt.ask("[bold yellow]Label (e.g. 'Math class')[/bold yellow]")

    slot_id = db.add_timetable_slot(day, start, end, label)
    rprint(f"[green]Slot #{slot_id} added: {DAYS[day]} {start}–{end} → {label}[/green]")


@timetable.command("ls")
@click.option("--day", "-d", default=-1, type=int, help="0=Mon..6=Sun, -1 for all")
def tt_ls(day):
    """Show your timetable."""
    slots = db.get_timetable(day_of_week=day if day >= 0 else None)
    if not slots:
        rprint("[yellow]No timetable entries found.[/yellow]")
        return
    table = Table(title="Your Timetable", header_style="bold cyan", border_style="cyan")
    table.add_column("ID",    justify="right", style="cyan")
    table.add_column("Day",   style="magenta")
    table.add_column("Start", style="green")
    table.add_column("End",   style="green")
    table.add_column("Label", style="white")
    for s in slots:
        table.add_row(str(s["id"]), DAYS[s["day"]], s["start"], s["end"], s["label"])
    console.print(table)


@timetable.command("rm")
@click.argument("slot_id", type=int)
def tt_rm(slot_id):
    """Remove a timetable slot."""
    if db.delete_timetable_slot(slot_id):
        rprint(f"[green]Slot #{slot_id} removed.[/green]")
    else:
        rprint(f"[red]Slot #{slot_id} not found.[/red]")


@timetable.command("check")
def tt_check():
    """Check if a planned time clashes with your timetable."""
    rprint("[bold cyan]Days: 0=Mon  1=Tue  2=Wed  3=Thu  4=Fri  5=Sat  6=Sun[/bold cyan]")
    day_str = Prompt.ask("[bold yellow]Day number (0-6)[/bold yellow]")
    try:
        day = int(day_str)
    except ValueError:
        rprint("[red]Invalid day.[/red]"); return

    start = Prompt.ask("[bold yellow]Planned start (HH:MM)[/bold yellow]")
    end   = Prompt.ask("[bold yellow]Planned end   (HH:MM)[/bold yellow]")

    clashes = db.check_timetable_clash(day, start, end)
    if not clashes:
        rprint(f"[bold green]No clashes! {DAYS[day]} {start}–{end} is free.[/bold green]")
    else:
        rprint(f"[bold red]Clash detected on {DAYS[day]} {start}–{end}![/bold red]")
        for c in clashes:
            rprint(f"  [red]• {c['start']}–{c['end']}: {c['label']}[/red]")


# ── Export ────────────────────────────────────────────────────────────────────

@cli.command("export")
@click.option("--format", "fmt", type=click.Choice(["csv", "markdown"]), default="csv")
def export(fmt):
    """Export all goals to CSV or Markdown."""
    if fmt == "csv":
        path = "lakshya_export.csv"
        db.export_to_csv(path)
        rprint(f"[green]Exported to [bold]{path}[/bold][/green]")
    else:
        goals = db.get_goals()
        path  = "lakshya_export.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write("# My Lakshyas\n\n")
            for g in goals:
                cb = "[x]" if g["status"] == "completed" else "[ ]"
                f.write(f"- {cb} **{g['title']}** ({g['type']}) — {g['progress']}%\n")
        rprint(f"[green]Exported to [bold]{path}[/bold][/green]")


if __name__ == "__main__":
    cli()
