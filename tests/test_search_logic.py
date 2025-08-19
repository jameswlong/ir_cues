# tests/test_search_logic.py

def _mk(rec_id, title, tags):
    return {"id": rec_id, "title": title, "tags": tags}

def _unquote(s: str) -> str:
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'") else s

def _run_query(idx, q_terms):
    required = [_unquote(t[1:]).casefold() for t in q_terms if t.startswith("+")]
    excluded = [_unquote(t[1:]).casefold() for t in q_terms if t.startswith("-")]
    optional = [_unquote(t).casefold() for t in q_terms if not t.startswith(("+","-"))]

    def hay(r):
        return (r["id"] + " " + r["title"] + " " + " ".join(r["tags"])).casefold()

    def match(r):
        h = hay(r)
        if any(req not in h for req in required): return False
        if any(exc in h for exc in excluded): return False
        if optional and not any(opt in h for opt in optional): return False
        return True

    return [r["id"] for r in idx if match(r)]

def test_boolean_search_phrases():
    idx = [
        _mk("windows/process/list", "Process list and triage", ["windows","process"]),
        _mk("windows/network/connections", "Active network connections", ["windows","network"]),
        _mk("linux/process/list", "Process list", ["linux","process"]),
        _mk("windows/persistence/autostarts", "Autostarts", ["windows","persistence"]),
    ]

    assert _run_query(idx, ['+windows', '-persistence', 'process']) == ['windows/process/list']
    assert _run_query(idx, ['+"active network"']) == ['windows/network/connections']
    assert _run_query(idx, ['+"process list"', '+windows']) == ['windows/process/list']
