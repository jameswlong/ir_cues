import os
import glob
import json
import yaml
import jinja2
import pytest

from ir_cues.loader import RECIPES_DIR, load_recipe
from ir_cues.renderer import render_recipe


def _all_recipe_paths():
    pattern = os.path.join(RECIPES_DIR, "**", "*.y*ml")
    return glob.glob(pattern, recursive=True)


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _rel_id_from_path(path: str) -> str:
    rel = os.path.relpath(path, RECIPES_DIR)
    rel_no_ext, _ = os.path.splitext(rel)
    return rel_no_ext.replace(os.sep, "/")  # IDs use forward slashes


def _mock_value(var_spec):
    if not isinstance(var_spec, dict):
        return "x"
    t = (var_spec.get("type") or "str").lower()
    if t in ("int", "integer"):
        return 1
    if t in ("float", "number"):
        return 1.0
    if t in ("bool", "boolean"):
        return True
    return "x"


def _build_vars(doc):
    vars_block = doc.get("vars", {}) or {}
    out = {}
    for k, spec in vars_block.items():
        if isinstance(spec, dict) and "default" in spec:
            out[k] = spec["default"]
        else:
            out[k] = _mock_value(spec)
    return out


@pytest.mark.parametrize("path", _all_recipe_paths())
def test_recipe_id_matches_path(path):
    doc = _load_yaml(path)
    assert isinstance(doc, dict), f"{path} did not parse to a dict"
    assert "id" in doc and isinstance(doc["id"], str) and doc["id"].strip(), f"{path}: missing 'id'"
    expected = _rel_id_from_path(path)
    actual = doc["id"].strip()
    assert actual == expected, f"ID must match path\nFile: {path}\nExpected: {expected}\nActual:   {actual}"


@pytest.mark.parametrize("path", _all_recipe_paths())
def test_recipe_schema_and_render(path):
    doc = _load_yaml(path)
    assert "id" in doc and "steps" in doc and isinstance(doc["steps"], list) and doc["steps"], f"{path}: invalid schema"

    # Steps must have render/include/include_step
    for i, step in enumerate(doc["steps"], start=1):
        has_any = any(k in step for k in ("render", "include", "include_step"))
        assert has_any, f"{path}: step {i} has neither 'render' nor 'include' nor 'include_step'"

        if "render" in step:
            assert isinstance(step["render"], dict) and step["render"], f"{path}: step {i} render must be dict"
            for variant, template in step["render"].items():
                assert isinstance(template, str) and template.strip(), f"{path}: step {i} variant '{variant}' empty"

    # Try loading through loader and rendering with mock vars
    via_loader = load_recipe(doc["id"])
    assert via_loader["id"] == doc["id"]

    vars_dict = _build_vars(doc)
    out_text = render_recipe(doc, vars_dict, format="text")
    assert isinstance(out_text, str) and out_text.strip(), f"{path}: empty text render"

    out_md = render_recipe(doc, vars_dict, format="md")
    assert "```" in out_md, f"{path}: markdown render missing code fence"

    # Compile each template with Jinja2 to catch syntax errors
    for i, step in enumerate(doc.get("steps", []), start=1):
        if "render" not in step:
            continue
        for variant, template in step["render"].items():
            try:
                jinja2.Template(template).render(**vars_dict)
            except Exception as e:
                pytest.fail(f"{path}: step {i} variant '{variant}' failed to render: {e}")