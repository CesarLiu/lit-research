#!/usr/bin/env python3
"""One reference numbering over several comparison tables, and the reference list for the numbers a report cites.

  python -I -X utf8 tools/survey_refs.py build OUT_REFS.json --results R1.json [R2.json ...] --rows ROWS_DIR1 [ROWS_DIR2 ...]
  python -I -X utf8 tools/survey_refs.py list REPORT.md REFS.json
  python -I -X utf8 tools/survey_refs.py company REPORT.md INDUSTRY_ROWS.json URLS.tsv [URLS2.tsv ...]

build  numbers every row of every ROWS_DIR (JSON rows with "id" and "title") in title order, 1..N, finds each paper's
       metadata (authors, year, DOI, venue) by title in the results files, and writes OUT_REFS.json
       [{n, id, title, short, first, year, doi, venue, table, authors}], the file split_claims.py reads.
       A row id used in two tables is an error. Unmatched titles are listed.
list   prints the reference list for the numbers [n] that REPORT.md cites (in number order, original numbers kept);
       it also lists cited numbers that do not exist.
Authors come from search metadata (mixed name orders; surname rule as in format_refs.py): check before submission.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from format_refs import norm, surname  # noqa: E402


def build(out: str, results: list[str], rows_dirs: list[str]) -> int:
    meta = {}
    for rp in results:
        for r in json.loads(Path(rp).read_text(encoding="utf-8"))["results"]:
            meta.setdefault(norm(r["title"]), r)
    rows, seen = [], {}
    for d in rows_dirs:
        for f in sorted(Path(d).glob("*.json")):
            r = json.loads(f.read_text(encoding="utf-8"))
            if r["id"] in seen:
                raise SystemExit(f"row id {r['id']} is in both {seen[r['id']]} and {d}")
            seen[r["id"]] = d
            rows.append((r, d))
    rows.sort(key=lambda x: x[0]["title"].lower())
    refs, missing = [], []
    for n, (r, d) in enumerate(rows, 1):
        rec = meta.get(norm(r["title"])) or next((v for k, v in meta.items() if k.startswith(norm(r["title"])[:45])), None)
        au = (rec or {}).get("authors") or []
        if rec is None:
            missing.append(r["title"])
        refs.append({"n": n, "id": r["id"], "title": r["title"], "short": re.split(r"[:\-–]", r["title"])[0].strip()[:40],
                     "first": (surname(au[0]) + (" et al." if len(au) > 1 else "")) if au else "",
                     "authors": au[:3] + (["et al."] if len(au) > 3 else []), "year": (rec or {}).get("year"),
                     "doi": (rec or {}).get("doi") or "", "venue": (rec or {}).get("venue") or "", "table": d})
    Path(out).write_text(json.dumps(refs, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(refs)} references -> {out}; no metadata for: {missing or 'none'}")
    return 0


def list_refs(report: str, refs_path: str) -> int:
    refs = {r["n"]: r for r in json.loads(Path(refs_path).read_text(encoding="utf-8"))}
    text = Path(report).read_text(encoding="utf-8")
    text = re.split(r"\n## References\b", text)[0]
    cited = sorted({int(x) for x in re.findall(r"\[(\d+)\]", text)})
    bad = [n for n in cited if n not in refs]
    for n in cited:
        r = refs.get(n)
        if not r:
            continue
        who = ", ".join(surname(a) if a != "et al." else a for a in r["authors"]).replace(", et al.", " et al.") or "(no authors in metadata)"
        doi = f" https://doi.org/{r['doi']}" if r["doi"] else ""
        venue = f" {r['venue']}." if r["venue"] else ""
        print(f"{n}. {who} ({r['year'] or 'n.d.'}). {r['title']}.{venue}{doi}")
    if bad:
        print(f"\nCITED BUT NOT NUMBERED: {bad}", file=sys.stderr)
    return 1 if bad else 0


def list_company(report: str, rows_json: str, tsvs: list[str]) -> int:
    """Appendix lines for the company codes ([W1] and so on) cited in the report: company, date, grade, quote, source URL."""
    rows = {r["id"]: r for r in json.loads(Path(rows_json).read_text(encoding="utf-8"))}
    url = {}
    for t in tsvs:
        for ln in Path(t).read_text(encoding="utf-8").splitlines():
            if ln.strip() and not ln.startswith("#"):
                f = ln.split("\t")
                url[f[0]] = f[3]
    text = re.split(r"\n## References\b", Path(report).read_text(encoding="utf-8"))[0]
    cited = sorted(set(re.findall(r"\[([A-Z]\d+)\]", text)), key=lambda c: (c[0], int(c[1:])))
    bad = [c for c in cited if c not in rows]
    for c in cited:
        r = rows.get(c)
        if r:
            print(f"- [{c}] {r['company']}, {r['date']}, grade {r['grade']}: \"{r['quote']}\" <{url.get(r['page'], 'url not recorded')}>")
    if bad:
        print(f"CITED BUT NOT IN ROWS: {bad}", file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 4 and a[0] == "company":
        raise SystemExit(list_company(a[1], a[2], a[3:]))
    if len(a) >= 5 and a[0] == "build" and "--results" in a and "--rows" in a:
        i, j = a.index("--results"), a.index("--rows")
        raise SystemExit(build(a[1], a[i + 1:j] if i < j else a[i + 1:], a[j + 1:i] if j < i else a[j + 1:]))
    if len(a) == 3 and a[0] == "list":
        raise SystemExit(list_refs(a[1], a[2]))
    print(__doc__)
    raise SystemExit(2)
