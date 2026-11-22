#!/usr/bin/env python3
"""Merge claim-check results with the claims and list everything that is not SUPPORTED.

  python -I -X utf8 tools/summarize_claims.py CLAIMS_DIR OUT.md

Reads claims_K.json and claims_result_K.json for every K. Checks that every claim has exactly one result with a valid
verdict, in the same order. Writes OUT.md: counts, then each non-SUPPORTED claim with its text, verdict and issue, then
the deterministic flags of claims the checker called SUPPORTED (a disagreement worth a second look).
Exit 1 if results are missing or malformed.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

VALID = {"SUPPORTED", "PARTIAL", "UNSUPPORTED", "NOT-CHECKABLE"}


def main(d: str, out: str) -> int:
    root = Path(d)
    claims, results, problems = [], {}, []
    for f in sorted(root.glob("claims_[0-9]*.json"), key=lambda p: int(re.findall(r"\d+", p.stem)[0])):
        k = re.findall(r"\d+", f.stem)[0]
        cl = json.loads(f.read_text(encoding="utf-8"))
        claims += cl
        rf = root / f"claims_result_{k}.json"
        if not rf.is_file():
            problems.append(f"missing {rf.name}")
            continue
        rs = json.loads(rf.read_text(encoding="utf-8"))
        if [r.get("id") for r in rs] != [c["id"] for c in cl]:
            problems.append(f"{rf.name}: ids do not match the claims in order")
        for r in rs:
            if r.get("verdict") not in VALID:
                problems.append(f"{rf.name}: claim {r.get('id')} has invalid verdict {r.get('verdict')!r}")
            results[r.get("id")] = r
    cnt = Counter(results[c["id"]]["verdict"] for c in claims if c["id"] in results)
    wrong = [c["id"] for c in claims if results.get(c["id"], {}).get("wrong_citation")]
    lines = ["# Claim check of the review", "",
             f"{len(claims)} claims, {len(results)} with a result. " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items())),
             f"Wrong citation reported for claims: {wrong or 'none'}", ""]
    lines.append("## Not SUPPORTED")
    for c in claims:
        r = results.get(c["id"])
        if r and r["verdict"] != "SUPPORTED":
            lines += [f"- **{c['id']} {r['verdict']}** [{c['section'][:30]}] {c['text']}", f"  - issue: {r.get('issue', '')}"]
    lines += ["", "## Flagged automatically but judged SUPPORTED (second look)"]
    for c in claims:
        r = results.get(c["id"])
        if r and r["verdict"] == "SUPPORTED" and c["flags"]:
            lines.append(f"- {c['id']} {'; '.join(c['flags'])} :: {c['text'][:100]}")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(lines[2])
    print("\n".join(problems) if problems else "results complete and well-formed")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]) if len(sys.argv) == 3 else print(__doc__) or 2)
