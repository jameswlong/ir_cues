# Contributing to ir-cues

Thanks for considering a contribution!  
This project is meant to stay **lightweight, practical, and easy to extend**.

---

## Ways to contribute

- Add new recipes (Windows, Linux, Cloud, Browser, IR hygiene).
- Improve existing recipes (fix commands, add hints, update last_tested).
- Report issues or suggest new use cases.
- Help improve docs and examples.

---

## Recipe guidelines

- Keep each recipe **one screen of output** or less.
- Prefer **built-in tools** (e.g. PowerShell, bash, sqlite3) over external binaries.
- Use **YAML schema**: `id`, `title`, `tags`, `vars`, `steps`.
- Use **Jinja2 variables** for anything user-specific: `{{ pid }}`, `{{ folder }}`, etc.
- Add `last_tested` with a date if you’ve verified it.
- Provide `hint` or `next` where pivoting makes sense.
- Tag recipes (`windows`, `linux`, `cloud`, `browser`, `ir`) to aid search.

Example minimal recipe:

```yaml
id: windows/example/recipe
title: Short description
tags: [windows, example]
vars:
  pid: {type: int, required: true}
steps:
  - name: Step description
    render:
      pwsh: |
        Get-Process -Id {{ pid }}
    hint: "Check parent PID for anomalies."