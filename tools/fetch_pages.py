#!/usr/bin/env python3
"""Fetch web pages to plain text so quotes can be checked later.

  python -I -X utf8 tools/fetch_pages.py URLS.tsv OUT_DIR

URLS.tsv: id <TAB> company <TAB> grade <TAB> url   (lines starting with # ignored)
Writes OUT_DIR/<id>.txt (first line: the URL) and prints status and size per page.
HTML: scripts/styles removed, tags stripped, entities decoded. PDF is not handled (marked).
"""
import html
import re
import sys
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (research-scan; plain text fetch)"


def to_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", raw)
    raw = re.sub(r"(?i)<br\s*/?>|</(p|div|li|h\d|tr|section|article)>", "\n", raw)
    raw = re.sub(r"(?s)<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    raw = re.sub(r"[ \t\r\f\v ]+", " ", raw)
    return re.sub(r"\n\s*\n+", "\n", raw).strip()


def main(tsv: str, out: str) -> int:
    outd = Path(out)
    outd.mkdir(parents=True, exist_ok=True)
    bad = 0
    for ln in open(tsv, encoding="utf-8"):
        if not ln.strip() or ln.startswith("#"):
            continue
        pid, company, grade, url = ln.rstrip("\n").split("\t")[:4]
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en"})
            with urllib.request.urlopen(req, timeout=30) as r:
                ctype = r.headers.get("Content-Type", "")
                data = r.read()
            if "pdf" in ctype.lower() or url.lower().endswith(".pdf"):
                print(f"{pid:14s} PDF not handled ({len(data)} bytes)")
                bad += 1
                continue
            text = to_text(data.decode("utf-8", errors="replace"))
            (outd / f"{pid}.txt").write_text(url + "\n" + text, encoding="utf-8")
            print(f"{pid:14s} ok {len(text):7d} chars  {company}")
            if len(text) < 1500:
                print(f"{'':14s} WARNING very short: probably JS-rendered or blocked")
                bad += 1
        except Exception as e:  # noqa: BLE001
            print(f"{pid:14s} FAIL {type(e).__name__}: {str(e)[:80]}")
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:3]) if len(sys.argv) == 3 else print(__doc__) or 2)
