#!/usr/bin/env python3
"""Numbered reference list (authors, year, title, venue, DOI) for the papers in a comparison table.

  python -I -X utf8 tools/format_refs.py RESULTS.json TABLE_DIR OUT.md

Order: the table rows sorted by title, so numbers match any text already citing [n].
Authors come from the search metadata, which mixes 'Given Family' and 'Family, Given'.
Surname rule: text before a comma if there is one, else the last word. Up to 3 surnames, then 'et al.'.
Names written in other orders (some East Asian names, particles like 'van der') can be wrong:
the list is for orientation and must be checked before submission.
"""
import glob
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def surname(name: str) -> str:
    name = name.strip()
    return name.split(",")[0].strip() if "," in name else name.split()[-1]


def main(results: str, table: str, out: str) -> int:
    by = {norm(r["title"]): r for r in json.loads(Path(results).read_text(encoding="utf-8"))["results"]}
    rows = sorted((json.loads(Path(f).read_text(encoding="utf-8")) for f in glob.glob(f"{table}/rows/*.json")),
                  key=lambda r: r["title"])
    lines, missing = [], []
    for n, r in enumerate(rows, 1):
        rec = by.get(norm(r["title"])) or next((v for k, v in by.items() if k.startswith(norm(r["title"])[:45])), None)
        if rec is None:
            missing.append(r["title"])
            continue
        au = rec.get("authors") or []
        who = ", ".join(surname(a) for a in au[:3]) + (" et al." if len(au) > 3 else "") if au else "(no authors in metadata)"
        doi = f" https://doi.org/{rec['doi']}" if rec.get("doi") else ""
        venue = f" {rec['venue']}." if rec.get("venue") else ""
        lines.append(f"{n}. {who} ({rec.get('year') or 'n.d.'}). {rec['title']}.{venue}{doi}")
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(lines)} references -> {out}; unmatched: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(main(*a) if len(a) == 3 else print(__doc__) or 2)
