#!/usr/bin/env python3
"""Check that every row quote occurs verbatim (whitespace-normalised) in its saved page.

  python -I -X utf8 tools/check_quotes.py ROWS.json PAGES_DIR

Also checks: grade A/B/C only, numbers in the claim occur in the quote or the page, ids unique.
Exit 1 if anything fails. Verbatim presence does not prove the claim is a fair reading of the quote.
"""
import json
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("‑", "-").replace("’", "'")).strip().lower()


def main(rows: str, pages: str) -> int:
    R = json.load(open(rows, encoding="utf-8"))
    bad, seen, cache = [], set(), {}
    for r in R:
        if r["id"] in seen:
            bad.append(f"{r['id']}: duplicate id")
        seen.add(r["id"])
        if r["grade"] not in ("A", "B", "C"):
            bad.append(f"{r['id']}: bad grade")
        f = Path(pages) / f"{r['page']}.txt"
        if not f.is_file():
            bad.append(f"{r['id']}: no page {r['page']}")
            continue
        page = cache.setdefault(f, norm(f.read_text(encoding="utf-8")))
        if norm(r["quote"]) not in page:
            bad.append(f"{r['id']}: quote NOT in {r['page']}: {r['quote'][:60]!r}")
        for n in re.findall(r"\d[\d,]*", r["claim"]):
            if n not in r["quote"] and n not in page:
                bad.append(f"{r['id']}: number {n} in claim not in page")
    print(f"{len(R)} rows, {len(bad)} problems")
    print("\n".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]) if len(sys.argv) == 3 else print(__doc__) or 2)
