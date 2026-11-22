#!/usr/bin/env python3
"""Build a paper-qa manifest CSV from resolve_oa.py's oa_report.json.

paper-qa (agent.index.manifest_file) accepts a CSV with file_location, doi, title
so it does not have to guess metadata with an LLM.

  file_location  path relative to the paper directory (the report's own folder)
  doi            from the report; for arXiv-only hits, derived from the arXiv id in
                 the download URL (10.48550/arXiv.<id>, the DataCite DOI); else blank
  title          from the report

Only items whose file exists are written. Nothing is guessed: if neither a DOI nor
an arXiv id is available, doi stays blank.

Usage:
    python -I -X utf8 tools/make_manifest.py runs/smoke-fulltext
"""
import csv
import json
import re
import sys
from pathlib import Path

ARXIV_URL = re.compile(r"arxiv\.org/(?:pdf|abs)/(\d{4}\.\d{4,5}|[a-z-]+(?:\.[A-Z]{2})?/\d{7})(?:v\d+)?", re.I)


def main(folder: str) -> int:
    d = Path(folder)
    report = json.loads((d / "oa_report.json").read_text(encoding="utf-8"))
    rows, skipped, derived = [], [], 0
    for it in report["items"]:
        if it.get("status") not in ("pdf", "txt"):
            continue
        f = it.get("file") or ""
        if not f or not (d / f).is_file():
            skipped.append(f or it.get("title", "?"))
            continue
        doi = (it.get("doi") or "").strip()
        if not doi:
            m = ARXIV_URL.search(it.get("url") or "")
            if m:
                doi, derived = f"10.48550/arXiv.{m.group(1)}", derived + 1
        rows.append({"file_location": f, "doi": doi, "title": " ".join((it.get("title") or "").split())})

    out = d / "manifest.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["file_location", "doi", "title"])
        w.writeheader()
        w.writerows(rows)

    blank = sum(1 for r in rows if not r["doi"])
    print(f"wrote {out}: {len(rows)} rows, {derived} DOIs derived from arXiv ids, {blank} blank DOI")
    if skipped:
        print(f"skipped (file missing): {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]) if len(sys.argv) > 1 else print(__doc__) or 2)
