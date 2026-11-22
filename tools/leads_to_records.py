#!/usr/bin/env python3
"""Turn screened chaining leads into search-result records, so the usual full-text steps can run on them.

  python -I -X utf8 tools/leads_to_records.py SCREENING.csv OUT_DIR

SCREENING.csv has the columns openalex_id and decision (rows whose decision starts with "include" are taken; made by hand
from chain_candidates.csv, see PIPELINE.md). The metadata of those works is fetched from OpenAlex in batches (no key, no
e-mail) and written to OUT_DIR/results.json in the shape fetch_papers.py writes, with found_by = ["chain"], so that
vendor/scripts/resolve_oa.py --from-json OUT_DIR/results.json can fetch open-access full text. Replies are cached in
OUT_DIR/cache. Works OpenAlex does not return are listed.
"""
import csv
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chain import API, Client, abstract  # noqa: E402

SEL = ("id,doi,title,publication_year,cited_by_count,abstract_inverted_index,authorships,primary_location,"
       "best_oa_location,open_access")


def main(screening: str, out: str) -> int:
    outd = Path(out)
    outd.mkdir(parents=True, exist_ok=True)
    ids = [r["openalex_id"] for r in csv.DictReader(open(screening, encoding="utf-8")) if r["decision"].startswith("include")]
    cl = Client(outd / "cache")
    works = {}
    for i in range(0, len(ids), 50):
        d = cl.get(f"{API}?" + urllib.parse.urlencode({"filter": "openalex:" + "|".join(ids[i:i + 50]), "per-page": 50, "select": SEL}))
        for w in d.get("results", []):
            works[w["id"].rsplit("/", 1)[-1]] = w
    recs, missing = [], [i for i in ids if i not in works]
    for i in ids:
        w = works.get(i)
        if not w:
            continue
        loc = w.get("best_oa_location") or w.get("primary_location") or {}
        recs.append({
            "source": "openalex", "sources": ["openalex"], "id": i,
            "doi": (w.get("doi") or "").replace("https://doi.org/", ""), "title": w.get("title") or "",
            "abstract": abstract(w.get("abstract_inverted_index")), "year": w.get("publication_year"),
            "authors": [(a.get("author") or {}).get("display_name") for a in (w.get("authorships") or [])[:20]],
            "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
            "cited_by": w.get("cited_by_count"), "is_oa": (w.get("open_access") or {}).get("is_oa"),
            "pdf_url": loc.get("pdf_url") or "", "url": w["id"], "found_by": ["chain"],
        })
    (outd / "results.json").write_text(json.dumps({"query": "citation chaining leads", "results": recs}, ensure_ascii=False, indent=1),
                                       encoding="utf-8")
    print(f"{len(recs)} records -> {outd / 'results.json'}; with pdf_url: {sum(1 for r in recs if r['pdf_url'])}, "
          f"with doi: {sum(1 for r in recs if r['doi'])}")
    if missing:
        print("not returned by OpenAlex:", missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]) if len(sys.argv) == 3 else print(__doc__) or 2)
