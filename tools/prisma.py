#!/usr/bin/env python3
"""PRISMA-style flow counts from the artefacts the pipeline already writes. Nothing is estimated.

  python -I -X utf8 tools/prisma.py SCREENING_LOG.csv FULLTEXT_DIR TABLE_DIR [OUT.md]

SCREENING_LOG.csv   from merge_results.py --log
FULLTEXT_DIR        resolve_oa.py output (oa_report.json)
TABLE_DIR           holds rows/*.json (one per paper in comparison table)
"""
import collections
import csv
import json
import sys
from pathlib import Path


def main(log: str, ft: str, table: str, out: str | None) -> int:
    rows = list(csv.DictReader(open(log, encoding="utf-8")))
    dup = sum(1 for r in rows if r["stage"] == "deduplication")
    flt = [r for r in rows if r["stage"] == "keyword filter"]
    inc = sum(1 for r in flt if r["decision"] == "include")
    why = collections.Counter(r["reason"] for r in flt if r["decision"] == "exclude")
    items = json.loads((Path(ft) / "oa_report.json").read_text(encoding="utf-8"))["items"]
    st = collections.Counter(i["status"] for i in items)
    got = st["pdf"] + st["txt"]
    n_rows = len(list((Path(table) / "rows").glob("*.json")))
    lines = [
        f"Records identified (all searches, before deduplication): {dup + len(flt)}",
        f"  removed as duplicates: {dup}",
        f"Records after deduplication: {len(flt)}",
        f"  excluded by keyword rule: {len(flt) - inc}",
        *[f"    {n}: {k}" for k, n in why.most_common()],
        f"Candidates after keyword rule: {inc}",
        f"  no usable identifier for full-text lookup: {inc - len(items)}",
        f"Full-text lookup attempted: {len(items)}",
        f"  open full text retrieved: {got} ({st['pdf']} PDF, {st['txt']} text)",
        f"  not retrieved: {len(items) - got} ({st['closed']} closed, {st['not-in-crossref']} DOI unknown to Crossref, {st['error']} errors)",
        f"Papers in comparison table: {n_rows}",
        f"  not tabled: {got - n_rows} of the retrieved (chosen by hand from ranked abstracts; per-paper reasons were not recorded)",
    ]
    text = "\n".join(lines)
    print(text)
    if out:
        Path(out).write_text("# Flow counts\n\n```\n" + text + "\n```\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(main(a[0], a[1], a[2], a[3] if len(a) > 3 else None) if len(a) >= 3 else print(__doc__) or 2)
