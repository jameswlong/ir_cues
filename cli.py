#ir_cues/cli.py
import json, sys
import typer
from rich.console import Console
from ir_cues.loader import load_index, load_recipe
from ir_cues.renderer import render_recipe

app = typer.Typer()
con = Console()

@app.command()
def list():
    idx = load_index()
    for r in idx:
        con.print(f"[bold]{r['id']}[/] - {', '.join(r.get('tags',[]))}")

@app.command()
def search(*terms: str):
    idx = load_index()
    hits = [r for r in idx if all(t.lower() in (r["id"]+" "+' '.join(r.get("tags",[]))).lower() for t in terms)]
    for r in hits:
        con.print(f"[bold]{r['id']}[/] - {r.get('title','')}" )

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