"""
finance_cli.py  --  CLI layer for Lakshya Finance Tracker
Click command group: finance_group  (registered as 'finance' in lakshya.py)
All output is ASCII-safe for Windows cp1252 terminals. No emoji, no unicode.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print as rprint
import finance_db

# Initialise DB tables on import
finance_db.init_finance_db()

console = Console()

CATEGORIES = ["food", "transport", "study", "fun", "health", "other"]


# -- Helpers ------------------------------------------------------------------

def _ascii_bar(pct, width=10):
    """Return an ASCII progress bar like [====------] for pct 0-100+."""
    filled = min(int(pct / 100 * width), width)
    return "[" + "=" * filled + "-" * (width - filled) + "]"


def _type_style(txn_type):
    return "bold green" if txn_type == "income" else "bold red"


# -- Command group -------------------------------------------------------------

@click.group("finance")
def finance_group():
    """Finance Tracker -- track income, expenses, budgets, and savings."""
    pass


# -- finance add --------------------------------------------------------------

@finance_group.command("add")
def finance_add():
    """Add an income or expense transaction (interactive)."""
    txn_type = Prompt.ask(
        "[bold yellow]Type?[/bold yellow]",
        choices=["income", "expense"],
        default="expense"
    )

    amount_str = Prompt.ask("[bold yellow]Amount (Rs.)?[/bold yellow]")
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        rprint("[red]Invalid amount. Must be a positive number.[/red]")
        return

    cat = Prompt.ask(
        "[bold yellow]Category?[/bold yellow]",
        choices=CATEGORIES,
        default="other"
    )
    note = Prompt.ask("[bold yellow]Note (optional)[/bold yellow]", default="")

    txn_id = finance_db.add_transaction(amount, txn_type, cat, note)

    color = "green" if txn_type == "income" else "red"
    body = (
        f"[bold white]Type    :[/bold white] [{color}]{txn_type.upper()}[/{color}]\n"
        f"[bold white]Amount  :[/bold white] [{color}]Rs. {amount:,.2f}[/{color}]\n"
        f"[bold white]Category:[/bold white] {cat}\n"
        f"[bold white]Note    :[/bold white] {note or '-'}"
    )
    console.print(Panel(
        body,
        title=f"[bold {color}] Transaction #{txn_id} Recorded [/bold {color}]",
        border_style=color,
        expand=False
    ))


# -- finance ls ---------------------------------------------------------------

@finance_group.command("ls")
def finance_ls():
    """List all transactions for the current month."""
    txns = finance_db.get_transactions()
    if not txns:
        rprint("[yellow]No transactions found for this month.[/yellow]")
        return

    table = Table(
        title="Transactions -- This Month",
        header_style="bold magenta",
        border_style="magenta",
        show_header=True
    )
    table.add_column("ID",       justify="right",  style="cyan",   no_wrap=True)
    table.add_column("Date",     style="white",     no_wrap=True)
    table.add_column("Type",     no_wrap=True)
    table.add_column("Category", style="yellow",    no_wrap=True)
    table.add_column("Amount",   justify="right",   no_wrap=True)
    table.add_column("Note",     style="dim")

    for t in txns:
        color = "bold green" if t["type"] == "income" else "bold red"
        type_cell = f"[{color}]{t['type'].upper()}[/{color}]"
        amt_cell  = f"[{color}]Rs. {t['amount']:,.2f}[/{color}]"
        table.add_row(
            str(t["id"]),
            t["date"],
            type_cell,
            t["category"],
            amt_cell,
            t["note"] or ""
        )

    console.print(table)


# -- finance summary ----------------------------------------------------------

@finance_group.command("summary")
def finance_summary():
    """Show a rich visual summary of income, expenses, and budgets this month."""
    from datetime import date as _date
    today = _date.today()
    month_name = today.strftime("%B %Y")

    s = finance_db.get_summary()

    income   = s["total_income"]
    expenses = s["total_expenses"]
    net      = s["net"]
    net_color = "green" if net >= 0 else "red"

    # Build top stats lines
    lines = [
        f"[bold white]Income  :[/bold white] [bold green]Rs. {income:>12,.2f}[/bold green]",
        f"[bold white]Expenses:[/bold white] [bold red]Rs. {expenses:>12,.2f}[/bold red]",
        f"[bold white]Net     :[/bold white] [bold {net_color}]Rs. {net:>12,.2f}[/bold {net_color}]",
        "",
    ]

    # Per-category breakdown
    warnings = []
    if s["per_category"]:
        lines.append("[bold cyan]-- Category Breakdown --[/bold cyan]")
        for cat, info in s["per_category"].items():
            spent  = info["spent"]
            budget = info["budget"]
            pct    = info["pct"]

            if budget is not None:
                bar   = _ascii_bar(pct)
                pct_s = f"{pct:5.1f}%"
                if pct > 100:
                    bar_colored = f"[bold red]{bar}[/bold red]"
                    warnings.append(cat)
                elif pct >= 80:
                    bar_colored = f"[bold yellow]{bar}[/bold yellow]"
                else:
                    bar_colored = f"[green]{bar}[/green]"
                lines.append(
                    f"  [yellow]{cat:<12}[/yellow] {bar_colored} {pct_s}"
                    f"  Rs.{spent:,.0f} / Rs.{budget:,.0f}"
                )
            else:
                lines.append(
                    f"  [yellow]{cat:<12}[/yellow] [dim]no budget set[/dim]"
                    f"  Rs.{spent:,.0f}"
                )
    else:
        lines.append("[dim]No transactions or budgets this month.[/dim]")

    if warnings:
        lines.append("")
        for w in warnings:
            lines.append(f"[bold yellow]  WARNING: '{w}' has exceeded its budget![/bold yellow]")

    body = "\n".join(lines)
    console.print(Panel(
        body,
        title=f"[bold magenta] Finance Summary -- {month_name} [/bold magenta]",
        border_style="magenta",
        expand=False
    ))


# -- finance budget -----------------------------------------------------------

@finance_group.command("budget")
def finance_budget():
    """Set a monthly spending budget for a category (interactive)."""
    cat = Prompt.ask(
        "[bold yellow]Category?[/bold yellow]",
        choices=CATEGORIES,
        default="other"
    )
    limit_str = Prompt.ask(f"[bold yellow]Monthly budget for '{cat}' (Rs.)?[/bold yellow]")
    try:
        limit = float(limit_str)
        if limit <= 0:
            raise ValueError
    except ValueError:
        rprint("[red]Invalid amount. Must be a positive number.[/red]")
        return

    finance_db.set_budget(cat, limit)
    rprint(f"[bold green]Budget set: '{cat}' = Rs. {limit:,.2f} / month[/bold green]")


# -- finance goal -------------------------------------------------------------

@finance_group.command("goal")
def finance_goal():
    """Create a savings goal linked to Lakshya's yearly goals."""
    title = Prompt.ask("[bold yellow]Savings goal title?[/bold yellow]")
    if not title.strip():
        rprint("[red]Title cannot be empty.[/red]")
        return

    target_str = Prompt.ask("[bold yellow]Target amount (Rs.)?[/bold yellow]")
    try:
        target = float(target_str)
        if target <= 0:
            raise ValueError
    except ValueError:
        rprint("[red]Invalid target amount.[/red]")
        return

    goal_id = finance_db.add_savings_goal(title, target)
    console.print(Panel(
        f"[bold white]{title}[/bold white]\n[dim]Target: Rs. {target:,.2f}[/dim]",
        title=f"[bold green] Savings Goal #{goal_id} Created! [/bold green]",
        border_style="green",
        expand=False
    ))


# -- finance rm ---------------------------------------------------------------

@finance_group.command("rm")
@click.argument("txn_id", type=int)
def finance_rm(txn_id):
    """Delete a transaction by its ID."""
    if finance_db.delete_transaction(txn_id):
        rprint(f"[green]Transaction #{txn_id} deleted.[/green]")
    else:
        rprint(f"[red]Transaction #{txn_id} not found.[/red]")
