#!/usr/bin/env python3
"""Retrieve -> summarize-and-score -> answer (paper-qa's RCS flow), with Claude Code as the LLM.

paper-qa calls an LLM to summarize and score each retrieved chunk against the question, keeps
the best few, then answers from only those with citation keys. This script does the two
deterministic halves; the LLM half (summarizing each chunk) is done by you or a Claude Code
subagent, so no API key is needed.

  prepare  papers dir (with manifest.csv) + question  ->  out/packets.jsonl
           Each line: {key, citation, pages, text, system, user}. Answer each packet with the
           JSON reply its `system` prompt asks for.
  collect  out/replies.jsonl ({"key": ..., "reply": "<raw LLM reply>"} per line)
           -> out/qa_prompt.md (best contexts + paper-qa's QA prompt) and out/contexts.json

Usage (from lit-review-baseline/):
  python -I -X utf8 tools/pqa/rcs.py prepare runs/smoke-fulltext "How is controllability achieved in driving scenario generation?" --out runs/rcs1
  python -I -X utf8 tools/pqa/rcs.py collect runs/rcs1
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I removes the script dir from sys.path
import pqa_port as pq  # noqa: E402


def read_pages(path: Path) -> dict[str, str]:
    if path.suffix.lower() == ".pdf":
        import pymupdf  # PyMuPDF

        with pymupdf.open(path) as doc:
            return {str(i + 1): page.get_text() for i, page in enumerate(doc)}
    return {"1": path.read_text(encoding="utf-8", errors="replace")}


def citation_of(row: dict) -> str:
    doi = f" doi:{row['doi']}" if row.get("doi") else ""
    return f"{row['title']}{doi}"


def key_of(file_location: str, i: int) -> str:
    return "pqac-" + hashlib.md5(f"{file_location}#{i}".encode()).hexdigest()[:8]  # noqa: S324


def prepare(a: argparse.Namespace) -> int:
    root = Path(a.papers)
    rows = list(csv.DictReader(open(root / "manifest.csv", encoding="utf-8")))
    chunks: list[dict] = []
    for row in rows:
        try:
            pages = read_pages(root / row["file_location"])
        except Exception as e:  # unreadable PDF: skip, say so
            print(f"skip {row['file_location']}: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        for i, c in enumerate(pq.chunk_pages(pages, a.chunk_chars, a.overlap)):
            if len(c["text"].strip()) < 200:
                continue
            c.update(key=key_of(row["file_location"], i), citation=citation_of(row), file=row["file_location"])
            chunks.append(c)
    index = pq.TfidfIndex([c["text"] for c in chunks])
    cands = index.search(a.question, a.fetch_k)
    picked = pq.mmr_select(index, cands, a.k, a.mmr_lambda)
    score = dict(cands)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    system = pq.SUMMARY_JSON_SYSTEM_PROMPT.format(summary_length=a.summary_length)
    with open(out / "packets.jsonl", "w", encoding="utf-8") as fh:
        for i in picked:
            c = chunks[i]
            user = pq.SUMMARY_JSON_USER_PROMPT.format(citation=c["citation"], text=c["text"].strip("\n"), question=a.question)
            rec = {"key": c["key"], "citation": c["citation"], "pages": c["pages"], "file": c["file"],
                   "tfidf": round(score[i], 4), "system": system, "user": user}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    (out / "question.txt").write_text(a.question, encoding="utf-8")
    print(f"{len(rows)} papers, {len(chunks)} chunks, {len(cands)} candidates, {len(picked)} packets -> {out/'packets.jsonl'}")
    print(f"papers covered: {len({chunks[i]['file'] for i in picked})}")
    return 0


def collect(a: argparse.Namespace) -> int:
    out = Path(a.out)
    question = (out / "question.txt").read_text(encoding="utf-8")
    packets = {p["key"]: p for p in map(json.loads, open(out / "packets.jsonl", encoding="utf-8"))}
    ctxs, bad = [], []
    for ln in open(out / "replies.jsonl", encoding="utf-8"):
        if not ln.strip():
            continue
        r = json.loads(ln)
        p = packets.get(r["key"])
        if p is None:
            bad.append((r["key"], "unknown key"))
            continue
        try:
            d = pq.llm_parse_json(r["reply"])
            summary = d.get("summary", "")
            score = d["relevance_score"] if "relevance_score" in d else pq.extract_score(summary)
        except (ValueError, KeyError) as e:
            bad.append((r["key"], str(e)[:80]))
            continue
        ctxs.append({"key": p["key"], "name": f"{p['file']} pages {p['pages']}", "citation": p["citation"],
                     "score": int(score), "summary": pq.strip_citations(summary)})
    ctxs.sort(key=lambda c: (-c["score"], c["name"]))
    kept = [c for c in ctxs[: a.max_sources] if c["score"] >= a.cutoff]
    if not kept:
        print(f"no context passed (cutoff {a.cutoff}); {pq.CANNOT_ANSWER_PHRASE} territory. unparsed: {bad}")
        return 1
    body = "\n\n".join(pq.CONTEXT_INNER_PROMPT.format(name=c["key"], text=c["summary"], citation=c["citation"]) for c in kept)
    context = pq.CONTEXT_OUTER_PROMPT.format(context_str=body, valid_keys=", ".join(c["key"] for c in kept))
    prompt = pq.QA_PROMPT.format(context=context, question=question, example_citation=f"({kept[0]['key']})",
                                 answer_length=a.answer_length)
    (out / "qa_prompt.md").write_text(prompt, encoding="utf-8")
    (out / "contexts.json").write_text(json.dumps(ctxs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(ctxs)} parsed, {len(kept)} kept (top {a.max_sources}, score>={a.cutoff}), unparsed: {bad or 'none'}")
    print(f"-> {out/'qa_prompt.md'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("papers")
    p.add_argument("question")
    p.add_argument("--out", required=True)
    p.add_argument("--k", type=int, default=pq.EVIDENCE_K)
    p.add_argument("--fetch-k", type=int, default=0, help="candidates before MMR (default 3*k)")
    p.add_argument("--mmr-lambda", type=float, default=0.9, help="our choice; >=1 disables diversity")
    p.add_argument("--chunk-chars", type=int, default=pq.CHUNK_CHARS)
    p.add_argument("--overlap", type=int, default=pq.CHUNK_OVERLAP)
    p.add_argument("--summary-length", default=pq.EVIDENCE_SUMMARY_LENGTH)
    c = sub.add_parser("collect")
    c.add_argument("out")
    c.add_argument("--max-sources", type=int, default=pq.ANSWER_MAX_SOURCES)
    c.add_argument("--cutoff", type=int, default=pq.EVIDENCE_RELEVANCE_SCORE_CUTOFF)
    c.add_argument("--answer-length", default=pq.ANSWER_LENGTH)
    a = ap.parse_args()
    if a.cmd == "prepare":
        a.fetch_k = a.fetch_k or 3 * a.k
        return prepare(a)
    return collect(a)


if __name__ == "__main__":
    raise SystemExit(main())
