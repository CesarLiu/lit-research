#!/usr/bin/env python3
"""Assemble comparison table B from rows/*.json and check each row against its evidence packet.

  python -I -X utf8 tools/assemble_table.py runs/tableB

Writes runs/tableB/table.md and runs/tableB/check.txt.
Checks per row: required fields, allowed control_family, page given when a value is filled,
value length (<= 45 words), and that every number in a value occurs in the packet text
(numbers not found are listed, since a number the packet does not contain was not read from it).
"""
import json
import re
import sys
from pathlib import Path

FAMILIES = {"reward/return conditioning", "inference-time guidance", "conditioning inputs (trained in)",
            "language/LLM-driven", "latent-space control", "RL fine-tuning", "none/uncontrolled", "other",
            "not stated in packet"}
FIELDS = ["control_signal", "control_mechanism", "base_model", "datasets", "metrics",
          "controllability_evidence", "stated_limitations"]
NA = "not stated in packet"
NUM = re.compile(r"\d+(?:\.\d+)?")


def cell(f: dict) -> str:
    v, p = f.get("value", ""), f.get("pages", "")
    v = v.replace("|", "/").replace("\n", " ")
    return v if v == NA else f"{v} (p.{p})"


def check_row(pid: str, r: dict, ptxt: str, families=None, fields=None) -> list[str]:
    """Problems of one row against its packet text (also used by llm_run.py to accept or retry a model reply).
    families and fields default to the scenario-table schema; a run folder can carry its own in schema.json."""
    families, fields = families or FAMILIES, fields or FIELDS
    issues = []
    if r.get("control_family") not in families:
        issues.append(f"{pid}: control_family {r.get('control_family')!r} not allowed")
    for k in fields:
        f = r.get(k)
        if not isinstance(f, dict) or "value" not in f:
            issues.append(f"{pid}: field {k} missing")
            continue
        v = f["value"]
        if v != NA and not str(f.get("pages", "")).strip():
            issues.append(f"{pid}: {k} has a value but no page")
        if len(v.split()) > 45:
            issues.append(f"{pid}: {k} longer than 45 words")
        nums = {n for n in NUM.findall(v)} - {n for n in NUM.findall(str(f.get('pages', '')))}
        missing = sorted(n for n in nums if n not in ptxt)
        if missing:
            issues.append(f"{pid}: {k} number(s) not in packet: {missing}")
    return issues


def load_schema(root: Path):
    """(families, fields) from root/schema.json {"families": [...], "fields": [...]} if present, else the defaults."""
    f = root / "schema.json"
    if not f.is_file():
        return FAMILIES, FIELDS
    d = json.loads(f.read_text(encoding="utf-8"))
    return set(d["families"]) | {NA}, list(d["fields"])


def main(root: str) -> int:
    root = Path(root)
    families, fields = load_schema(root)
    rows, issues = [], []
    for fp in sorted((root / "rows").glob("*.json")):
        try:
            r = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(f"{fp.stem}: invalid JSON ({e})")
            continue
        pid = fp.stem
        packet = (root / "packets" / f"{pid}.md")
        ptxt = packet.read_text(encoding="utf-8") if packet.is_file() else ""
        if not ptxt:
            issues.append(f"{pid}: packet missing")
        issues += check_row(pid, r, ptxt, families, fields)
        rows.append(r)
    ids = {fp.stem for fp in (root / "packets").glob("*.md")}
    for m in sorted(ids - {fp.stem for fp in (root / "rows").glob("*.json")}):
        issues.append(f"{m}: no row written")

    rows.sort(key=lambda r: (r.get("control_family", ""), r.get("title", "")))
    if fields == FIELDS:
        head = ["Paper", "Family", "Control signal", "Mechanism", "Base model", "Data", "Metrics", "Evidence of control", "Stated limits"]
    else:
        head = ["Paper", "Family"] + [f.replace("_", " ").capitalize() for f in fields]
    lines = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for r in rows:
        lines.append("| " + " | ".join([r.get("title", "?").replace("|", "/"), r.get("control_family", "?")]
                                        + [cell(r.get(k, {})) for k in fields]) + " |")
    (root / "table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (root / "check.txt").write_text("\n".join(issues) + ("\n" if issues else "no issues\n"), encoding="utf-8")
    print(f"{len(rows)} rows -> {root/'table.md'}; {len(issues)} issue(s) -> {root/'check.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]) if len(sys.argv) > 1 else print(__doc__) or 2)
