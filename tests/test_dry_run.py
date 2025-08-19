# tests/test_dry_run.py
import json
from ir_cues.loader import load_recipe
from ir_cues.renderer import collect_commands

def test_collect_commands_flatten_includes():
    rec = load_recipe("windows/process/list")
    seq = collect_commands(rec, {})
    assert isinstance(seq, list) and len(seq) > 0
    # at least one pwsh or cmd present
    assert any(s["variant"] in ("pwsh","cmd","bash","kql") for s in seq)

def test_collect_commands_filters_vars():
    rec = load_recipe("windows/process/triage")
    seq = collect_commands(rec, {"pid": 1})
    # all commands should have the rendered pid
    assert any("ProcessId=1" in s["command"] or " -Id 1" in s["command"] for s in seq)
