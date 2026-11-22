#!/usr/bin/env python3
"""For papers resolve_oa.py found closed, look for the same paper on arXiv by exact title and fetch that open copy.

  python -I -X utf8 tools/arxiv_fallback.py FULLTEXT_DIR

Reads FULLTEXT_DIR/oa_report.json. For every item with status "closed" it asks the arXiv API for the title (3 s between
requests); a hit counts only if the title matches almost word for word (similarity 0.95 or more). The PDF is downloaded
from arxiv.org/pdf/<id> (it must start with %PDF-), and the item is rewritten as status "pdf", via "arxiv-title", with the
arXiv id in "url". Nothing behind a paywall is touched; this uses only the preprint the authors posted. A title match is
not proof of identity: the arXiv version can differ from the published one, so the report keeps the DOI of the original.
"""
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_citations_arxiv as va  # noqa: E402

THRESHOLD = 0.95


def main(ft: str) -> int:
    root = Path(ft)
    rep_path = root / "oa_report.json"
    rep = json.loads(rep_path.read_text(encoding="utf-8"))
    got = 0
    for it in rep["items"]:
        if it.get("status") != "closed":
            continue
        try:
            meta, score = va.arxiv_by_title(it["title"])
        except Exception as e:  # noqa: BLE001
            print(f"  ? {it['title'][:60]}: arXiv query failed ({type(e).__name__})")
            time.sleep(3)
            continue
        time.sleep(3)
        if not meta or score < THRESHOLD:
            print(f"  - {it['title'][:60]}: no arXiv copy (best similarity {score:.2f})")
            continue
        aid = meta["DOI"].split("arXiv.")[-1]
        url = f"https://arxiv.org/pdf/{aid}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "lit-baseline/1.0"}), timeout=90) as r:
                data = r.read()
        except Exception as e:  # noqa: BLE001
            print(f"  ! {it['title'][:60]}: download failed ({type(e).__name__})")
            continue
        if not data.startswith(b"%PDF-"):
            print(f"  ! {it['title'][:60]}: not a PDF")
            continue
        name = f"arxiv_{aid.replace('/', '_')}.pdf"
        (root / name).write_bytes(data)
        it.update(status="pdf", via="arxiv-title", url=url, file=name, bytes=len(data))
        got += 1
        print(f"  + {it['title'][:60]}: arXiv {aid} (similarity {score:.2f}, {len(data) // 1024} KB)")
    counts = {}
    for it in rep["items"]:
        counts[it["status"]] = counts.get(it["status"], 0) + 1
    rep["resolved"] = counts
    rep_path.write_text(json.dumps(rep, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{got} more open copies from arXiv; now {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]) if len(sys.argv) == 2 else print(__doc__) or 2)
