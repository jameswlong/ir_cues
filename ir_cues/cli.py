#ir_cues/cli.py
from __future__ import annotations
import json, sys
import typer
from typing import List, Optional
from rich.console import Console
from ir_cues.loader import load_index, load_recipe
from ir_cues.renderer import render_recipe

app = typer.Typer()
con = Console()

# ---- list command (don't shadow built-in list) ----
@app.command("list")  # CLI: ir-cues list
def list_cmd():
    idx = load_index()
    for r in idx:
        con.print(f"[bold]{r['id']}[/] - {r.get('title','')}")


# ---- search command with variadic args ----
@app.command()
def search(
    terms: list[str] = typer.Argument(
        ..., help="Search terms (+require, -exclude, plain=optional). Quotes form phrases."
    )
) -> None:
    idx = load_index()

    required: list[str] = []
    excluded: list[str] = []
    optional: list[str] = []

    def _clean(term: str) -> str:
        t = term.strip()
        # drop one leading + or -
        prefix = t[0] if t[:1] in "+-" else ""
        body = t[1:] if prefix else t
        # strip surrounding single/double quotes if present
        if len(body) >= 2 and body[0] == body[-1] and body[0] in ("'", '"'):
            body = body[1:-1]
        return prefix, body.casefold()

    for raw in terms:
        prefix, body = _clean(raw)
        if not body:
            continue
        if prefix == "+":
            required.append(body)
        elif prefix == "-":
            excluded.append(body)
        else:
            optional.append(body)

    def haystack(rec: dict) -> str:
        return " ".join([
            rec.get("id", ""),
            rec.get("title", ""),
            " ".join(rec.get("tags", [])),
        ]).casefold()

    def matches(rec: dict) -> bool:
        h = haystack(rec)
        if any(req not in h for req in required):
            return False
        if any(exc in h for exc in excluded):
            return False
        if optional and not any(opt in h for opt in optional):
            return False
        return True

    hits = [r for r in idx if matches(r)]
    if not hits:
        con.print("[dim]No matches.[/]")
        raise typer.Exit(code=0)

    for r in hits:
        title = r.get("title", "")
        tags = ", ".join(r.get("tags", []))
        con.print(f"[bold]{r['id']}[/] - {title} [dim]({tags})[/]") 

@app.command()
def show(recipe_id: str):
    r = load_recipe(recipe_id)
    con.print_json(data={"id": r["id"], "vars": r.get("vars", {})})

@app.command()
def run(recipe_id: str,
        vars: str = typer.Option("", help="JSON dict of variables"),
        format: str = typer.Option("text", help="text|md"),
        copy: bool = typer.Option(False, help="Copy to clipboard")):
    r = load_recipe(recipe_id)
    v = json.loads(vars or "{}")
    out = render_recipe(r, v, format=format)
    if copy:
        try:
            import pyperclip; pyperclip.copy(out)
        except Exception:
            pass
    con.print(out)

@app.command()
def dry_run(
    recipe_id: str = typer.Argument(..., help="Recipe ID to expand"),
    vars: str = typer.Option("", help="JSON dict of variables"),
    variant: Optional[str] = typer.Option(None, help="Filter by variant: pwsh|cmd|bash|kql|..."),
    format: str = typer.Option("text", help="text|md")
):
    """
    Examples:
    # Show full plan
    ir-cues dry-run incident/host/windows-baseline

    # Only PowerShell commands
    ir-cues dry-run incident/host/windows-baseline --variant pwsh

    # Markdown plan, with vars
    ir-cues dry-run windows/process/triage --vars '{"pid":4321}' --format md
    """
    import json
    rec = load_recipe(recipe_id)
    v = json.loads(vars or "{}")
    seq = collect_commands(rec, v)

    if variant:
        seq = [s for s in seq if s["variant"] == variant]

    if not seq:
        con.print("[dim]No commands produced.[/]")
        raise typer.Exit(code=0)

    if format == "md":
        # markdown checklist
        con.print(f"# Plan for `{recipe_id}`\n")
        for i, s in enumerate(seq, 1):
            con.print(f"**{i}. {s['id']} — {s['step']}**  \n*{s['variant']}*\n")
            con.print("```")
            con.print(s["command"])
            con.print("```\n")
        con.print(f"\nTotal: {len(seq)} commands.")
    else:
        # rich table
        table = Table(show_header=True, header_style="bold")
        table.add_column("#", width=4)
        table.add_column("Recipe")
        table.add_column("Step")
        table.add_column("Variant", width=10)
        table.add_column("Command")
        for i, s in enumerate(seq, 1):
            table.add_row(str(i), s["id"], s["step"], s["variant"], s["command"])
        con.print(table)
        con.print(f"[dim]Total: {len(seq)} commands.[/]")

if __name__ == "__main__":
    app()