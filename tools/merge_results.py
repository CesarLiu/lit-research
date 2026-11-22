#!/usr/bin/env python3
"""Merge several fetch_papers.py results.json files into one deduplicated, optionally filtered list.

  python -I -X utf8 tools/merge_results.py OUT.json IN1.json IN2.json ... [--known known.txt] [--filter] [--log screening_log.csv]

Dedup order: DOI (lower case), arXiv id, normalised title. Each kept record gets `found_by` (input names).
--filter keeps records whose title+abstract hit a driving term AND a scenario/simulation term
(a transparent keyword rule, not a model; see DRIVE/TASK below). A tighter rule was tried and lost 2 of 16 known papers, so the loose one stays..
--known: text file, one title per line. Prints which of them each stage contains (title word containment >= 0.8).
"""
import json
import re
import sys
from pathlib import Path

DRIVE = re.compile(r"\b(driv\w*|traffic|vehicle\w*|autonomous|self-driving|av|ads|motion forecasting|trajector\w*)\b", re.I)
TASK = re.compile(r"\b(scenario\w*|scene\w*|simulat\w*|generat\w*|behaviou?r\w*|agent\w*|adversarial|safety-critical)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def arxiv_of(r: dict) -> str:
    if r.get("source") == "arxiv" and r.get("id"):
        return re.sub(r"v\d+$", "", r["id"])
    m = re.search(r"10\.48550/arxiv\.(.+)", (r.get("doi") or "").lower())
    return m.group(1) if m else ""


def keys(r: dict) -> list[str]:
    ks = []
    if r.get("doi"):
        ks.append("doi:" + r["doi"].lower())
    if arxiv_of(r):
        ks.append("ax:" + arxiv_of(r))
    if norm(r.get("title")):
        ks.append("t:" + norm(r["title"]))
    return ks


def has(titles: list[str], known: str) -> bool:
    kt = set(norm(known).split())
    return any(len(kt & set(norm(t).split())) / len(kt) >= 0.8 for t in titles)


def main(argv: list[str]) -> int:
    flt = "--filter" in argv
    known_path = argv[argv.index("--known") + 1] if "--known" in argv else None
    log_path = argv[argv.index("--log") + 1] if "--log" in argv else None
    args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] not in ("--known", "--log"))]
    out, ins = args[0], args[1:]
    kept: list[dict] = []
    index: dict[str, dict] = {}
    raw = 0
    log: list[dict] = []  # one row per decision, for the screening log
    for path in ins:
        name = Path(path).parent.name
        for r in json.loads(Path(path).read_text(encoding="utf-8"))["results"]:
            raw += 1
            hit = next((index[k] for k in keys(r) if k in index), None)
            if hit is None:
                hit = dict(r, found_by=[])
                kept.append(hit)
            else:  # fill gaps from the duplicate
                log.append({"input": name, "title": r["title"], "doi": r.get("doi", ""), "stage": "deduplication",
                            "decision": "exclude", "reason": "duplicate of: " + hit["title"][:70]})
                for f in ("doi", "pdf_url", "abstract"):
                    if not hit.get(f) and r.get(f):
                        hit[f] = r[f]
            if name not in hit["found_by"]:
                hit["found_by"].append(name)
            for k in keys(hit):
                index.setdefault(k, hit)
    def verdict(r: dict) -> str:
        """'' if the record passes the keyword rule, else the reason it fails."""
        text = r["title"] + " " + (r.get("abstract") or "")
        miss = [n for n, rx in (("driving/traffic term", DRIVE), ("scenario/simulation term", TASK)) if not rx.search(text)]
        return "no " + " and no ".join(miss) if miss else ""

    final = []
    for r in kept:
        why = verdict(r) if flt else ""
        if flt:
            log.append({"input": "|".join(r["found_by"]), "title": r["title"], "doi": r.get("doi", ""), "stage": "keyword filter",
                        "decision": "exclude" if why else "include", "reason": why})
        if not why:
            final.append(r)
    print(f"inputs {len(ins)}, raw {raw}, unique {len(kept)}, after filter {len(final)}" + ("" if flt else " (no filter)"))
    multi = sum(1 for r in kept if len(r["found_by"]) > 1)
    print(f"found by more than one input: {multi}")
    if known_path:
        known = [ln.strip() for ln in open(known_path, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
        t_all, t_fin = [r["title"] for r in kept], [r["title"] for r in final]
        print(f"known papers: {len(known)}; in unique set {sum(has(t_all, k) for k in known)}; in final {sum(has(t_fin, k) for k in known)}")
        for k in known:
            print(f"  {'Y' if has(t_fin, k) else ('f' if has(t_all, k) else '-')} {k}")
        print("  (Y in final, f found but removed by filter, - not retrieved)")
    if log_path:
        import csv
        with open(log_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["input", "title", "doi", "stage", "decision", "reason"])
            w.writeheader()
            w.writerows(log)
        print(f"screening log: {len(log)} rows -> {log_path}")
    Path(out).write_text(json.dumps({"query": "merged", "results": final}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
