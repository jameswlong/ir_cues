import os
import glob
import json
import types

import pytest
import yaml
import jinja2

# Adjust if your package name/path differs
from dfir_cues.loader import RECIPES_DIR, load_recipe
from dfir_cues.renderer import render_recipe


def all_recipe_paths():
    pattern = os.path.join(RECIPES_DIR, "**", "*.y*ml")
    return glob.glob(pattern, recursive=True)


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def rel_id_from_path(path: str) -> str:
    rel = os.path.relpath(path, RECIPES_DIR)
    # drop extension
    rel_no_ext, _ = os.path.splitext(rel)
    # normalize to forward slashes for IDs
    return rel_no_ext.replace(os.sep, "/")

def mock_value(var_spec):
    """
    Return a safe mock value based on the 'type' field in a var spec.
    Defaults if type not provided: string.
    """
    if not isinstance(var_spec, dict):
        return "x"
    t = (var_spec.get("type") or "str").lower()
    if t in ("int", "integer"):
        return 1
    if t in ("float", "number"):
        return 1.0
    if t in ("bool", "boolean"):
        return True
    # strings, paths, ids
    return "x"


def build_vars(doc):
    """
    Build a vars dict:
    - Use defaults where present
    - Otherwise fill with mock values based on 'type'
    """
    vars_block = doc.get("vars", {}) or {}
    out = {}
    for k, spec in vars_block.items():
        if isinstance(spec, dict) and "default" in spec:
            out[k] = spec["default"]
        else:
            out[k] = mock_value(spec)
    return out

def test_recipe_id_matches_path():
    mismatches = []
    for path in all_recipe_paths():
        doc = load_yaml(path)
        assert isinstance(doc, dict), f"{path} did not parse to a dict"
        assert "id" in doc and isinstance(doc["id"], str) and doc["id"].strip(), f"{path}: missing 'id'"
        expected = rel_id_from_path(path)
        actual = doc["id"].strip()
        if actual != expected:
            mismatches.append(f"\n- ID: '{actual}'\n  Path: '{expected}'\n  File: {path}")
    assert not mismatches, "Recipe ID must match path (relative to RECIPES_DIR):" + "".join(mismatches)
Tips:


@pytest.mark.parametrize("path", all_recipe_paths())
def test_recipe_schema_minimal(path):
    doc = load_yaml(path)
    assert isinstance(doc, dict), f"{path} did not parse to a dict"

    # Required
    assert "id" in doc and isinstance(doc["id"], str) and doc["id"].strip(), f"{path}: missing 'id'"
    assert "steps" in doc and isinstance(doc["steps"], list) and doc["steps"], f"{path}: 'steps' must be a non-empty list"

    # Optional but recommended
    assert "title" in doc and isinstance(doc["title"], str), f"{path}: missing or invalid 'title'"

    # Steps must have a render dict (at least one variant)
    for i, step in enumerate(doc["steps"], start=1):
        assert isinstance(step, dict), f"{path}: step {i} must be a dict"
        assert "render" in step and isinstance(step["render"], dict) and step["render"], f"{path}: step {i} needs a non-empty 'render' dict"
        # Templates should be strings
        for variant, template in step["render"].items():
            assert isinstance(template, str) and template.strip(), f"{path}: step {i} variant '{variant}' must be a non-empty string"


@pytest.mark.parametrize("path", all_recipe_paths())
def test_recipe_renders_with_mock_vars(path):
    doc = load_yaml(path)
    vars_dict = build_vars(doc)

    # Ensure load_recipe can find by id
    via_loader = load_recipe(doc["id"])
    assert via_loader["id"] == doc["id"]

    # Try rendering. Use text first.
    out = render_recipe(doc, vars_dict, format="text")
    assert isinstance(out, str) and len(out) > 0, f"{path}: empty render output"

    # Try markdown too
    out_md = render_recipe(doc, vars_dict, format="md")
    assert "```" in out_md, f"{path}: markdown render did not include code fences"

    # Try Jinja2 compilation on each template to catch syntax early
    for i, step in enumerate(doc["steps"], start=1):
        for variant, template in step["render"].items():
            try:
                jinja2.Template(template).render(**vars_dict)
            except Exception as e:
                pytest.fail(f"{path}: step {i} variant '{variant}' failed to render with mock vars: {e}")

def test_composed_recipe_renders():
    from dfir_cues.loader import load_recipe
    from dfir_cues.renderer import render_recipe
    doc = load_recipe("incident/host/quick-trriage")
    out = render_recipe(doc, {"suspect_pid": 1}, format="text")
    assert "Logged-on users" in out and "Active TCP/UDP" in out
    
def test_include_step_pulls_single_variant():
    from dfir_cues.loader import load_recipe
    from dfir_cues.renderer import render_recipe
    doc = {
        "id": "tmp/composite/test",
        "title": "tmp",
        "steps": [
            {
                "include_step": {
                    "id": "windows/process/triage",
                    "step": "Hash binary",
                    "variant": "pwsh",
                    "vars": {"pid": "1"},
                    "format": "text",
                },
                "title": "just hash",
            }
        ],
    }
    out = render_recipe(doc, {}, "text")
    assert "Get-FileHash" in out