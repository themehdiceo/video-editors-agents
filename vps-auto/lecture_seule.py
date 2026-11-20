#!/usr/bin/env python3
"""Hook PreToolUse sur Supabase execute_sql : LECTURE SEULE et projet PPC seulement (Mehdi 20/11). Code 2 = refusé."""
import json, re, sys

PROJET = "zbpvlcqfzanjflabpggf"
INTERDIT = r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|call|do|vacuum|comment|merge|refresh|set|lock)\b"


def verdict(entree: dict) -> str | None:
    t = entree.get("tool_input", {})
    if t.get("project_id") != PROJET:
        return f"projet {t.get('project_id')} interdit (seul {PROJET})"
    q = re.sub(r"--[^\n]*|/\*.*?\*/", " ", t.get("query", ""), flags=re.S).strip().lower()
    if not re.match(r"(select|with)\b", q) or re.search(INTERDIT, q) or ";" in q.rstrip("; \n")[:-1]:
        return "lecture seule : une seule requête SELECT"
    return None


if __name__ == "__main__":
    if sys.argv[1:] == ["test"]:
        assert verdict({"tool_input": {"project_id": PROJET, "query": "select 1"}}) is None
        assert verdict({"tool_input": {"project_id": PROJET, "query": "with a as (select 1) select * from a;"}}) is None
        assert verdict({"tool_input": {"project_id": PROJET, "query": "delete from public.ppc_leads"}})
        assert verdict({"tool_input": {"project_id": PROJET, "query": "select 1; drop table x"}})
        assert verdict({"tool_input": {"project_id": "autre", "query": "select 1"}})
        print("test OK")
        sys.exit(0)
    raison = verdict(json.load(sys.stdin))
    if raison:
        print(raison, file=sys.stderr)
        sys.exit(2)
