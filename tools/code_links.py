#!/usr/bin/env python3
"""List code-host links (GitHub, GitLab, Hugging Face) found in evidence packets.

  python -I -X utf8 tools/code_links.py OUT.csv PACKETS_DIR [PACKETS_DIR ...]

One row per packet: id, the first link found, and where ("first pages" for the first two pages of the paper, "later in
packet only" for a link found only in the retrieved passages, which may be another paper's code). Packets are partial
excerpts, so a missing link does not mean the paper has no code, and a link is not checked to work. The same rule as
ledger.py's code_url column.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import code_link  # noqa: E402


def main(out: str, dirs: list[str]) -> int:
    rows = []
    for d in dirs:
        for f in sorted(Path(d).glob("*.md")):
            url, where = code_link(f.read_text(encoding="utf-8"))
            rows.append({"id": f.stem, "packet_dir": d, "url": url, "where": where})
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, ["id", "packet_dir", "url", "where"])
        w.writeheader()
        w.writerows(rows)
    n = sum(1 for r in rows if r["url"])
    first = sum(1 for r in rows if r["where"] == "first pages")
    print(f"{len(rows)} packets, {n} with a code-host link ({first} on the first pages) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2:]) if len(sys.argv) >= 3 else print(__doc__) or 2)
