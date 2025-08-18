from dfir_cues.loader import load_recipe as _load_recipe
import jinja2

def _render_text_block(kind: str, content: str, fmt: str) -> str:
    if fmt == "md":
        return f"```{kind}\n{content}\n```"
    return f"{kind.upper()}:\n{content}"

def _select_step(doc: dict, selector):
    steps = doc.get("steps", [])
    if isinstance(selector, int):
        idx = selector - 1
        if idx < 0 or idx >= len(steps):
            raise IndexError(f"Step {selector} out of range (1..{len(steps)})")
        return steps[idx]
    if isinstance(selector, str):
        for st in steps:
            if st.get("name") == selector:
                return st
        raise KeyError(f"Step named '{selector}' not found")
    raise TypeError("step selector must be int (1-based) or str (step name)")

def render_recipe(recipe: dict, vars: dict, format: str = "text", _stack=None) -> str:
    _stack = _stack or []
    rid = recipe.get("id", "<unknown>")
    if rid in _stack:
        return f"[!] Cycle detected including {rid}. Skipping.\n"
    _stack = _stack + [rid]

    out = []
    title = recipe.get("title", rid)
    out.append(f"# {title}\n")

    for i, step in enumerate(recipe.get("steps", []), start=1):
        name = step.get("name") or step.get("title") or f"Step {i}"
        out.append(f"[{i}] {name}")

        if "render" in step:
            for variant, template in step["render"].items():
                try:
                    rendered = jinja2.Template(template).render(**vars)
                except Exception as e:
                    rendered = f"ERROR: {e}"
                out.append(_render_text_block(variant, rendered, format))

        elif "include" in step:
            inc = step["include"]
            child_id = inc["id"]
            child_vars = {**vars, **{k: jinja2.Template(str(v)).render(**vars)
                                     for k, v in (inc.get("vars") or {}).items()}}
            child_fmt = inc.get("format", format)
            try:
                child = _load_recipe(child_id)
                rendered = render_recipe(child, child_vars, child_fmt, _stack=_stack)
            except Exception as e:
                rendered = f"[!] Failed to include {child_id}: {e}"
            out.append(rendered)

        elif "include_step" in step:
            inc = step["include_step"]
            child_id = inc["id"]
            selector = inc["step"]
            child_fmt = inc.get("format", format)
            only_variant = inc.get("variant")
            child_vars = {**vars, **{k: jinja2.Template(str(v)).render(**vars)
                                     for k, v in (inc.get("vars") or {}).items()}}
            try:
                child = _load_recipe(child_id)
                sub = _select_step(child, selector)
                if "render" not in sub or not isinstance(sub["render"], dict):
                    raise ValueError("selected step has no render block")
                # Render either one variant or all
                variants = {only_variant: sub["render"][only_variant]} if only_variant else sub["render"]
                for variant, template in variants.items():
                    try:
                        rendered = jinja2.Template(template).render(**child_vars)
                    except Exception as e:
                        rendered = f"ERROR: {e}"
                    out.append(_render_text_block(variant, rendered, child_fmt))
            except Exception as e:
                out.append(f"[!] Failed to include step from {child_id}: {e}")

        else:
            out.append("[!] Step has neither 'render', 'include', nor 'include_step'.")

        if "hint" in step:
            out.append(f"Hint: {step['hint']}")
        if "next" in step:
            out.append("Next pivots: " + ", ".join(step["next"]))
        out.append("")

    return "\n".join(out)