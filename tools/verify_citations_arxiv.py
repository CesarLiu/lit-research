#!/usr/bin/env python3
"""verify_citations with arXiv support. Wraps the unmodified vendor script.

Upstream resolves DOIs only through Crossref, where arXiv papers (DataCite DOIs
10.48550/arXiv.*) do not exist, so every real arXiv paper looks invented.

What this adds, without touching vendor/:
  1. A line with an arXiv id (DOI form, 'arXiv:2403.19918', or arxiv.org/abs/..)
     is resolved through the arXiv API. An id that resolves counts like a DOI:
     CONFIRMED. An id that does not exist falls through to the title path.
  2. Title lookup also searches arXiv and keeps the better of the two candidates.
     It still never returns CONFIRMED from a title: TITLE MATCH needs a human.
  3. Retraction check still runs (OpenAlex is queried with the arXiv DOI).

Known limit (same as upstream): when a line holds both an id and a title, only
the id is checked. A real id with a wrong title is therefore CONFIRMED.

Usage (from lit-review-baseline/):
    python -I -X utf8 tools/verify_citations_arxiv.py citations.txt
"""
from __future__ import annotations

import importlib.util
import re
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

VENDOR = Path(__file__).resolve().parent.parent / "vendor" / "verify" / "verify_citations.py"
spec = importlib.util.spec_from_file_location("vendor_verify", VENDOR)
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

NEW_ID = r"\d{4}\.\d{4,5}"
OLD_ID = r"[a-z-]+(?:\.[A-Z]{2})?/\d{7}"
ID = rf"(?:{NEW_ID}|{OLD_ID})"
ARXIV_DOI_RE = re.compile(rf"10\.48550/arxiv\.({ID})(?:v\d+)?", re.I)
ARXIV_TEXT_RE = re.compile(rf"(?:arxiv[:\s]*|arxiv\.org/(?:abs|pdf)/)({ID})(?:v\d+)?", re.I)
ATOM = {"a": "http://www.w3.org/2005/Atom"}
_last_call = [0.0]


def _arxiv_query(params: dict) -> list[ET.Element]:
    # arXiv asks for ~1 request per 3 seconds.
    wait = 3.0 - (time.time() - _last_call[0])
    if wait > 0:
        time.sleep(wait)
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": v.UA})
    root = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                root = ET.fromstring(r.read())
            break
        except Exception:
            time.sleep(2 * (attempt + 1))
    _last_call[0] = time.time()
    return root.findall("a:entry", ATOM) if root is not None else []


def _to_meta(entry: ET.Element) -> dict | None:
    eid = entry.findtext("a:id", "", ATOM)
    title = " ".join((entry.findtext("a:title", "", ATOM) or "").split())
    if "/api/errors" in eid or not title or title.lower() == "error":
        return None
    aid = re.sub(r"v\d+$", "", eid.split("/abs/")[-1])
    authors = [
        {"family": (n.findtext("a:name", "", ATOM) or "?").split()[-1]}
        for n in entry.findall("a:author", ATOM)
    ]
    year = (entry.findtext("a:published", "", ATOM) or "")[:4]
    return {
        "DOI": f"10.48550/arXiv.{aid}",
        "title": [title],
        "author": authors,
        "issued": {"date-parts": [[int(year)]]} if year.isdigit() else {},
        "container-title": ["arXiv"],
    }


def arxiv_by_id(aid: str) -> dict | None:
    entries = _arxiv_query({"id_list": aid, "max_results": 1})
    return _to_meta(entries[0]) if entries else None


def arxiv_by_title(title: str) -> tuple[dict | None, float]:
    t = " ".join(title.split())[:200]
    best, best_score = None, 0.0
    for e in _arxiv_query({"search_query": f'ti:"{t}"', "max_results": 5}):
        m = _to_meta(e)
        if not m:
            continue
        s = v.similar(t, m["title"][0])
        if v.norm(t) == v.norm(m["title"][0]):
            s += 0.001  # exact ordered match wins ties against bag-of-words overlap
        if s > best_score:
            best, best_score = m, s
    return best, best_score


_orig_by_doi, _orig_by_title = v.by_doi, v.by_title


_claimed: deque[str] = deque()  # one entry per input line that has a DOI, in order (upstream main() calls by_doi once per such line)


def _strip_ids(line: str) -> str:
    line = v.DOI_RE.sub(" ", line)
    line = ARXIV_TEXT_RE.sub(" ", line)
    return re.sub(r"\b(?:doi|arxiv)\b", " ", line, flags=re.I)


def title_agrees(claimed: str, resolved: str) -> bool:
    """True if the line's own text is consistent with the title the id resolves to.

    Idea from paper-qa: title and authors are checked, not just an identifier. Here a
    containment test (not Jaccard) because lines also carry authors/venue/year noise.
    Short lines (under 4 words besides the id) say nothing about the title, so pass.
    """
    c, r = set(v.norm(claimed).split()), set(v.norm(resolved).split())
    if len(c) < 4 or not r:
        return True
    return len(r & c) / len(r) >= 0.5 or len(r & c) / len(c) >= 0.5


def by_doi(doi: str):
    m = ARXIV_DOI_RE.fullmatch(doi)
    meta = arxiv_by_id(m.group(1)) if m else _orig_by_doi(doi)
    claimed = _claimed.popleft() if _claimed else None
    if meta is not None and claimed and not title_agrees(claimed, (meta.get("title") or [""])[0]):
        print(f"! ID/TITLE MISMATCH  {doi} resolves to: {v.describe(meta)}")
        print(f"                     but the line says: {claimed.strip()[:100]}")
        return None  # fall through to the title path; never CONFIRMED
    return meta


def by_title(title: str):
    cr, cr_score = _orig_by_title(title)
    ax, ax_score = arxiv_by_title(title)
    if ax is not None and ax_score > cr_score:
        return ax, min(ax_score, 1.0)
    return cr, cr_score


v.by_doi, v.by_title = by_doi, by_title


def preprocess(src: str) -> str:
    """Turn 'arXiv:ID' / arxiv.org/abs/ID mentions into the DOI form upstream looks for."""
    out = []
    for ln in open(src, encoding="utf-8"):
        s = ln.rstrip("\n")
        if s.strip() and not s.startswith("#") and not v.DOI_RE.search(s):
            m = ARXIV_TEXT_RE.search(s)
            if m:
                s += f" 10.48550/arXiv.{m.group(1)}"
        d = v.DOI_RE.search(s) if s.strip() and not s.startswith("#") else None
        if d:
            _claimed.append(_strip_ids(s))
        out.append(s)
    tmp = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    tmp.write("\n".join(out) + "\n")
    tmp.close()
    return tmp.name


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    sys.argv[1] = preprocess(sys.argv[1])
    try:
        raise SystemExit(v.main())
    finally:
        Path(sys.argv[1]).unlink(missing_ok=True)
