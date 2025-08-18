import json
import subprocess
import sys
import os


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "ir_cues.cli", *args],
        capture_output=True, text=True, check=True
    )


def test_cli_list_runs():
    out = run_cli("list").stdout
    assert out.strip(), "Expected some recipes listed"


def test_cli_show_and_run_smoke():
    # Find one known recipe id to smoke test; adjust if you rename
    recipe_id = "incident/host/linux-quick-triage"

    show = run_cli("show", recipe_id).stdout
    assert "vars" in show.lower()

    # Provide minimal vars payload
    vars_json = json.dumps({"pid": 1})
    run_out = run_cli("run", recipe_id, "--vars", vars_json).stdout
    assert "Get-CimInstance" in run_out or run_out.strip(), "Run output looked empty"
