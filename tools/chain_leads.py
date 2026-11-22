#!/usr/bin/env python3
"""List chaining leads that are new, in the search window, on topic by the strict rule and linked to at least 3 seeds,
with their OpenAlex abstracts, for hand screening.

  python -I -X utf8 tools/chain_leads.py

Reads runs/chain/chain_candidates.csv and the cached OpenAlex replies in runs/chain/cache; writes runs/chain/leads_n3.json
(sorted by number of seed links) and prints one line per lead. Paths are fixed to the first run; edit them for another topic."""
import csv
import glob
import json
import sys

sys.path.insert(0, "tools")
from chain import abstract  # noqa: E402

ab = {}
for f in glob.glob("runs/chain/cache/*.json"):
    try:
        d = json.load(open(f, encoding="utf-8"))
    except Exception:
        continue
    items = d.get("results") if isinstance(d, dict) else None
    if items is None and isinstance(d, dict) and "id" in d:
        items = [d]
    for w in items or []:
        i = (w.get("id") or "").rsplit("/", 1)[-1]
        a = abstract(w.get("abstract_inverted_index"))
        if i and a and i not in ab:
            ab[i] = a
R = list(csv.DictReader(open("runs/chain/chain_candidates.csv", encoding="utf-8")))
S = [r for r in R if r["in_corpus"] == "0" and r["in_window"] == "1" and r["on_topic_tight"] == "1" and int(r["n_seeds"]) >= 3]
S.sort(key=lambda r: (-int(r["n_seeds"]), -int(r["cited_by_count"])))
json.dump([{**r, "abstract": ab.get(r["id"], "")} for r in S], open("runs/chain/leads_n3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print(len(S), "leads;", sum(1 for r in S if ab.get(r["id"])), "with abstract")
for k, r in enumerate(S, 1):
    print(f"{k:3d}|{r['n_seeds']}|{r['year']}|{r['title'][:88]}| {ab.get(r['id'], '')[:170]}")
