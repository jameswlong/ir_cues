#ir_cues/cli.py
import json, sys
import typer
from typing import List
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
def search(terms: List[str] = typer.Argument(..., help="Search terms")):
    """
    Search recipe id, title, and tags.
    Usage: ir-cues search windows process
    """
    idx = load_index()
    q = [t.casefold() for t in terms]

    def matches(rec: dict) -> bool:
        hay = " ".join([
            rec.get("id", ""),
            rec.get("title", ""),
            " ".join(rec.get("tags", [])),
        ]).casefold()
        return all(t in hay for t in q)

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

if __name__ == "__main__":
    app()