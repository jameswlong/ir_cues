#ir_cues/renderer.py

import jinja2
from rich.console import Console

console = Console()

def render_recipe(recipe: dict, vars: dict, format: str = "text") -> str:
    """Render a recipe with variable substitution."""
    output = []

    title = recipe.get("title", recipe["id"])
    output.append(f"# {title}\n")

    steps = recipe.get("steps", [])
    for i, step in enumerate(steps, start=1):
        name = step.get("name", f"Step {i}")
        output.append(f"[{i}] {name}")

        render = step.get("render", {})
        for variant, template in render.items():
            try:
                rendered = jinja2.Template(template).render(**vars)
            except Exception as e:
                rendered = f"ERROR: {e}"

            if format == "md":
                block = f"```{variant}\n{rendered}\n```"
            else:
                block = f"{variant.upper()}:\n{rendered}"

            output.append(block)

        if "hint" in step:
            output.append(f"Hint: {step['hint']}")
        if "next" in step:
            output.append("Next pivots: " + ", ".join(step["next"]))

        output.append("")  # spacing

    return "\n".join(output)
