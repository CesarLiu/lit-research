#!/usr/bin/env python3
"""Build one evidence packet per paper for filling a comparison table (one row per paper).

For each selected paper: the first two pages (title, abstract, intro) plus, for each field
query, the best 2 chunks *within that paper* (TF-IDF, from pqa_port). Output is plain markdown
that a reader (Claude or a subagent) answers from, with page numbers kept.

  python -I -X utf8 tools/table_packets.py FULLTEXT_DIR SELECTION.txt OUT_DIR

SELECTION.txt: one line per paper, a substring of its title (case-insensitive, must match exactly one
oa_report item with a downloaded file), optionally followed by " # reason it was selected".
Lines starting with # are ignored.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "pqa"))
import pqa_port as pq  # noqa: E402

FIELD_QUERIES = {
    "control": "control controllable conditioning condition guidance guided user specify steer cross-attention token language prompt reward tilt",
    "model": "we propose model architecture diffusion autoregressive transformer VAE flow matching reinforcement learning network encoder decoder",
    "data": "dataset datasets trained evaluated Waymo nuScenes nuPlan Argoverse WOMD INTERACTION highD experiments setup",
    "metrics": "metrics evaluation realism collision rate offroad minADE JSD success rate diversity results table compared baselines",
    "limits": "limitation limitations future work fail failure case discussion conclusion drawback",
}


def read_pages(path: Path) -> dict[str, str]:
    if path.suffix.lower() == ".pdf":
        import pymupdf

        with pymupdf.open(path) as doc:
            return {str(i + 1): p.get_text() for i, p in enumerate(doc)}
    return {"1": path.read_text(encoding="utf-8", errors="replace")}


def main(ft: str, sel: str, out: str) -> int:
    root, outd = Path(ft), Path(out)
    outd.mkdir(parents=True, exist_ok=True)
    items = [x for x in json.loads((root / "oa_report.json").read_text(encoding="utf-8"))["items"]
             if x.get("status") in ("pdf", "txt") and x.get("file") and (root / x["file"]).is_file()]
    # "Title substring  # reason" : the reason (after ' #') is the recorded selection reason and is not matched
    wanted = [ln.split(" #")[0].strip() for ln in open(sel, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
    made, problems = [], []
    for w in wanted:
        hits = [x for x in items if w.lower() in x["title"].lower()]
        if len(hits) != 1:
            problems.append(f"{w!r}: {len(hits)} matches (no downloaded full text, or ambiguous)")
            continue
        it = hits[0]
        pages = read_pages(root / it["file"])
        chunks = [c for c in pq.chunk_pages(pages, 2500, 200) if len(c["text"].strip()) > 150]
        index = pq.TfidfIndex([c["text"] for c in chunks])
        first = "\n".join(pages[p] for p in list(pages)[:2])[:7000]
        parts = [f"# {it['title']}\nfile: {it['file']}  doi: {it.get('doi') or 'n/a'}\n",
                 f"## First pages (pages 1-2)\n{first}\n"]
        used = set()
        for field, q in FIELD_QUERIES.items():
            got = [i for i, _ in index.search(q, 6) if i not in used][:2]
            used.update(got)
            parts.append(f"## Passages for: {field}")
            for i in got:
                parts.append(f"[pages {chunks[i]['pages']}]\n{chunks[i]['text'].strip()}\n")
        pid = re.sub(r"[^a-z0-9]+", "_", it["title"].lower())[:50].strip("_")
        (outd / f"{pid}.md").write_text("\n".join(parts), encoding="utf-8")
        made.append(pid)
    print(f"{len(made)} packets in {outd}")
    for p in problems:
        print("PROBLEM", p)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:4]) if len(sys.argv) == 4 else print(__doc__) or 2)
