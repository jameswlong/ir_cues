import pathlib
import yaml
import pytest

RECIPES_DIR = pathlib.Path(__file__).parent.parent / "ir_cues" / "recipes"

def _all_yaml_files():
    return list(RECIPES_DIR.rglob("*.yaml"))

def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _extract_commands(doc):
    """
    Yield (recipe_id, step_index, variant, command_string).
    """
    rid = doc.get("id", "<unknown>")
    for idx, step in enumerate(doc.get("steps", []), start=1):
        if "render" not in step:
            continue
        render_block = step["render"]
        for variant, cmd in render_block.items():
            # normalise whitespace
            norm = "\n".join(line.rstrip() for line in cmd.strip().splitlines())
            yield rid, idx, variant, norm

def test_no_duplicate_commands_across_all_recipes():
    seen = {}
    duplicates = []

    for path in _all_yaml_files():
        doc = _load(path)
        for rid, idx, variant, cmd in _extract_commands(doc):
            key = (variant, cmd)
            if key in seen:
                duplicates.append(
                    f"Duplicate {variant} command:\n"
                    f"- {seen[key][0]} step {seen[key][1]}\n"
                    f"- {rid} step {idx}\n"
                    f"--- Command ---\n{cmd}\n"
                )
            else:
                seen[key] = (rid, idx)

    if duplicates:
        pytest.fail("Duplicate commands found:\n\n" + "\n".join(duplicates))
