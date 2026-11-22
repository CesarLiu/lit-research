#!/usr/bin/env python3
"""Run the three structured LLM steps of the pipeline against an OpenAI-compatible endpoint (vLLM, llama.cpp
server, Ollama, or any hosted service with /v1/chat/completions), instead of Claude sub-agents.

  python -I -X utf8 tools/llm_run.py STEP RUN_DIR [options]

STEP      extract_row | atomic_claims | audit_cells | claim_check   (prompts are RUN_DIR/prompts/STEP.md, the same files
                                                             that `prep_agents.py render` gives to Claude sub-agents)
Options    --base-url URL   default env LLM_BASE_URL or http://localhost:8000/v1
           --model NAME     default env LLM_MODEL (required; vLLM needs the served model name)
           --api-key-env V  name of the env var that holds the key (default LLM_API_KEY; unset = no auth header)
           --out-dir DIR    where outputs go (default RUN_DIR). Existing output files are never overwritten
                            unless --force
           --only ID ...    only these items (packet ids, cell numbers, claim ids)
           --group FILE     extract_row: only the ids listed in this file (e.g. g1.txt)
           --workers N      parallel requests (default 4)      --timeout S  per request (default 300)
           --max-tokens N   (default 2048)                    --json-mode  send response_format=json_object
           --retries N      re-ask with the problems listed (default 2)
           --max-prompt-chars N  skip items whose prompt is longer (default 120000)
           --dry-run        print the first prompt (system + user) and exit; no network

Each item is one request. The reply must be one JSON object; it is checked with the same code as the Claude path
(assemble_table.check_row for rows; verdict sets for audit and claim checks) and re-asked with the problems listed.
Outputs have the same names and shapes as the Claude path, so assemble_table.py, summarize_claims.py and the rest
work unchanged. Every request is logged to OUT_DIR/llm_log.jsonl with the model name, so the model is on record.
The checking steps (audit_cells, claim_check) should use a different model from extract_row; this tool does not
enforce that, it only records which model ran.
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_table import check_row  # noqa: E402
from ledger import check_claims  # noqa: E402

VERDICTS = {"SUPPORTED", "PARTIAL", "UNSUPPORTED"}
CLAIM_VERDICTS = VERDICTS | {"NOT-CHECKABLE"}


# ------------------------------------------------------------------ prompts: file-agent template -> inline template
def paragraphs(t: str) -> list[str]:
    return [p for p in t.strip().split("\n\n")]


def to_api(step: str, template: str) -> str:
    """The Claude path tells an agent to read and write files. Here the data is in the message and the reply is the
    JSON, so the paragraphs about files are replaced; every rule paragraph is kept word for word."""
    out = []
    for p in paragraphs(template):
        if step == "extract_row":
            if p.startswith("Input:"):
                p = ("Input: the evidence packet of one paper is in the user message. A packet holds the paper's first two "
                     "pages plus the best passages from the paper for five topics. Passages are labelled [pages X-Y].")
            elif p.startswith("Output:"):
                p = re.sub(r"^Output:[^\n]*", "Output: reply with ONLY this JSON object (valid JSON, no text before or after it):", p)
            elif p.startswith("When done"):
                continue
            p = p.replace("\n- Do not edit any other file.", "")
        elif step == "atomic_claims":
            if p.startswith("Input:"):
                p = ("Input: the evidence packet of one paper is in the user message. A packet holds the paper's first two "
                     "pages plus the best passages from the paper for five topics. Passages are labelled [pages X-Y].")
            elif p.startswith("Output:"):
                p = re.sub(r"^Output:[^\n]*", "Output: reply with ONLY this JSON object (valid JSON, no text before or after it):", p)
            elif p.startswith("When done"):
                continue
            p = p.replace("\n- Do not edit any other file.", "")
        elif step == "audit_cells":
            if p.startswith("Input:"):
                p = ("Input: one cell in the user message: the packet text, and the table cell as JSON with \"field\", "
                     "\"claimed_value\", \"claimed_pages\".")
            elif p.startswith("For each cell, read the packet"):
                p = p.replace("For each cell, read the packet", "Read the packet")
                p = p.replace("report PAGE-MISMATCH if not", "set \"page_mismatch\" to true if not")
            elif p.startswith("Be skeptical"):
                p = re.sub(r" Do not edit any file except the output below\.", "", p)
            elif p.startswith("Write "):
                p = ("Reply with ONLY one JSON object: {\"verdict\": \"SUPPORTED\"|\"PARTIAL\"|\"UNSUPPORTED\", "
                     "\"page_mismatch\": true/false, \"issue\": \"one short sentence, empty if SUPPORTED and pages OK\"}")
            elif p.startswith("Reply with at most"):
                continue
        elif step == "claim_check":
            if p.startswith("Input:"):
                p = ("Input: one claim in the user message, as JSON, followed by the evidence it needs: the full rows of the "
                     "papers it cites and, for claims that cite nothing or many papers, the whole table and the process files.")
            elif p.startswith("Evidence you may use"):
                p = ("Evidence you may use, and nothing else: the evidence sections of the user message (row files of the cited "
                     "papers; table.md; PRISMA.md; selection.txt). Do not use outside knowledge about the papers.")
            elif p.startswith("Write "):
                p = ("Reply with ONLY one JSON object: {\"id\", \"verdict\", \"wrong_citation\": true/false, \"issue\": \"one short "
                     "sentence naming the problem and the row field, empty if SUPPORTED\"}.")
            elif p.startswith("Reply with at most"):
                continue
        out.append(p)
    text = "\n\n".join(out)
    if "{RUN_DIR}" in text or "{GROUP_FILE}" in text or "{RESULT_FILE}" in text or ".json containing" in text:
        raise SystemExit(f"template {step}: a file instruction is left in the inline prompt; update to_api()")
    return text + "\n"


# ------------------------------------------------------------------ requests
def chat(cfg, system: str, messages: list[dict]) -> tuple[str, dict]:
    body = {"model": cfg.model, "messages": [{"role": "system", "content": system}] + messages,
            "temperature": 0, "max_tokens": cfg.max_tokens}
    if cfg.json_mode:
        body["response_format"] = {"type": "json_object"}
    headers = {"Content-Type": "application/json"}
    key = os.environ.get(cfg.api_key_env, "")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(cfg.base_url.rstrip("/") + "/chat/completions", json.dumps(body).encode("utf-8"), headers)
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout) as r:
            d = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]!r}") from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        raise RuntimeError(f"cannot reach {cfg.base_url}: {e}") from None
    return d["choices"][0]["message"]["content"] or "", d.get("usage") or {}


def parse_json(text: str):
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(t)
    except ValueError:
        i, j = t.find("{"), t.rfind("}")
        if 0 <= i < j:
            return json.loads(t[i:j + 1])
        raise


def ask(cfg, step: str, item: str, system: str, user: str, validate, log):
    """One item: up to 1+retries requests. validate(obj) -> (hard_problems, soft_problems). Returns (obj, problems)."""
    msgs = [{"role": "user", "content": user}]
    obj, problems = None, []
    for attempt in range(cfg.retries + 1):
        t0 = time.time()
        try:
            text, usage = chat(cfg, system, msgs)
        except RuntimeError as e:
            log({"step": step, "item": item, "attempt": attempt, "ok": False, "error": str(e)})
            return None, [str(e)]
        try:
            obj = parse_json(text)
            hard, soft = validate(obj)
        except ValueError as e:
            obj, hard, soft = None, [f"reply is not valid JSON ({e})"], []
        problems = hard + soft
        log({"step": step, "item": item, "attempt": attempt, "ok": not problems, "problems": problems,
             "usage": usage, "seconds": round(time.time() - t0, 1)})
        if not problems:
            return obj, []
        msgs += [{"role": "assistant", "content": text},
                 {"role": "user", "content": "Your reply has these problems:\n- " + "\n- ".join(problems)
                  + "\nReply again with ONLY the corrected JSON object."}]
    return (obj if obj is not None and not hard else None), problems  # soft problems only: keep the last reply


# ------------------------------------------------------------------ steps
def step_extract_row(cfg, run: Path, system: str, log):
    ids = sorted(p.stem for p in (run / "packets").glob("*.md"))
    if cfg.group:
        ids = [i for i in ids if i in {x.strip() for x in open(cfg.group, encoding="utf-8")}]
    if cfg.only:
        ids = [i for i in ids if i in cfg.only]
    outd = Path(cfg.out_dir or run) / "rows"
    outd.mkdir(parents=True, exist_ok=True)
    todo = [i for i in ids if cfg.force or not (outd / f"{i}.json").exists()]
    print(f"extract_row: {len(ids)} packets, {len(ids) - len(todo)} rows already exist and are kept, {len(todo)} to do")

    def work(pid):
        ptxt = (run / "packets" / f"{pid}.md").read_text(encoding="utf-8")
        if len(ptxt) > cfg.max_prompt_chars:
            return pid, None, [f"packet too long ({len(ptxt)} chars)"]

        def validate(r):
            if not isinstance(r, dict):
                return ["reply is not a JSON object"], []
            r["id"] = pid
            iss = check_row(pid, r, ptxt)
            hard = [i for i in iss if "not allowed" in i or "missing" in i]
            return hard, [i for i in iss if i not in hard]

        obj, probs = ask(cfg, "extract_row", pid, system, ptxt, validate, log)
        if obj is not None:
            obj["id"] = pid
            (outd / f"{pid}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
        return pid, obj, probs

    return run_pool(cfg, todo, work, "row")


def step_atomic_claims(cfg, run: Path, system: str, log):
    ids = sorted(p.stem for p in (run / "packets").glob("*.md"))
    if cfg.group:
        ids = [i for i in ids if i in {x.strip() for x in open(cfg.group, encoding="utf-8")}]
    if cfg.only:
        ids = [i for i in ids if i in cfg.only]
    outd = Path(cfg.out_dir or run) / "atomic"
    outd.mkdir(parents=True, exist_ok=True)
    todo = [i for i in ids if cfg.force or not (outd / f"{i}.json").exists()]
    print(f"atomic_claims: {len(ids)} packets, {len(ids) - len(todo)} files already exist and are kept, {len(todo)} to do")

    def work(pid):
        ptxt = (run / "packets" / f"{pid}.md").read_text(encoding="utf-8")
        if len(ptxt) > cfg.max_prompt_chars:
            return pid, None, [f"packet too long ({len(ptxt)} chars)"]

        def validate(obj):
            if isinstance(obj, dict):
                obj["id"] = pid
            return check_claims(pid, obj, ptxt)

        obj, probs = ask(cfg, "atomic_claims", pid, system, ptxt, validate, log)
        if obj is not None:
            (outd / f"{pid}.json").write_text(json.dumps(obj, indent=1, ensure_ascii=False), encoding="utf-8")
        return pid, obj, probs

    return run_pool(cfg, todo, work, "paper")


def step_audit_cells(cfg, run: Path, system: str, log):
    cells = json.loads((run / "audit_cells.json").read_text(encoding="utf-8"))
    out = Path(cfg.out_dir or run) / "audit_result.json"
    if out.exists() and not cfg.force:
        raise SystemExit(f"{out} exists; use --force or another --out-dir")
    idx = [i for i in range(len(cells)) if not cfg.only or str(i + 1) in cfg.only]

    def work(i):
        c = cells[i]
        ptxt = (run / c["packet"]).read_text(encoding="utf-8")
        user = f"PACKET TEXT:\n{ptxt}\n\nCELL:\n{json.dumps({k: c[k] for k in ('field', 'claimed_value', 'claimed_pages')}, ensure_ascii=False)}"
        if len(user) > cfg.max_prompt_chars:
            return i, None, [f"prompt too long ({len(user)} chars)"]

        def validate(r):
            if not isinstance(r, dict) or r.get("verdict") not in VERDICTS or not isinstance(r.get("page_mismatch"), bool):
                return ['need {"verdict": SUPPORTED|PARTIAL|UNSUPPORTED, "page_mismatch": true/false, "issue": "..."}'], []
            return [], []

        obj, probs = ask(cfg, "audit_cells", str(i + 1), system, user, validate, log)
        return i, obj, probs

    res = run_pool(cfg, idx, work, "cell")
    results = [dict(packet=cells[i]["packet"], field=cells[i]["field"], verdict=o["verdict"], page_mismatch=o["page_mismatch"],
                    issue=o.get("issue", "")) for i, o, _ in res if o]
    if len(results) == len(cells):
        Path(cfg.out_dir or run).mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    else:
        print(f"audit_result.json NOT written: {len(results)} of {len(cells)} cells have a valid reply")
    return res


def step_claim_check(cfg, run: Path, system: str, log):
    cdir = run / "claims"
    chunks = sorted(cdir.glob("claims_[0-9]*.json"))
    outd = Path(cfg.out_dir or cdir)
    outd.mkdir(parents=True, exist_ok=True)
    rows_all = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (run / "rows").glob("*.json")}
    extra = {n: (run / n).read_text(encoding="utf-8") for n in ("table.md", "selection.txt") if (run / n).is_file()}
    prisma = Path(cfg.prisma) if cfg.prisma else run.parent / "corpus2" / "PRISMA.md"
    if prisma.is_file():
        extra["PRISMA.md"] = prisma.read_text(encoding="utf-8")
    all_res = []
    for ch in chunks:
        k = re.findall(r"\d+", ch.stem)[0]
        target = outd / f"claims_result_{k}.json"
        if target.exists() and not cfg.force:
            print(f"{target.name} exists, kept")
            continue
        claims = json.loads(ch.read_text(encoding="utf-8"))
        claims = [c for c in claims if not cfg.only or str(c["id"]) in cfg.only]

        def work(c):
            parts = [f"CLAIM:\n{json.dumps({k2: c[k2] for k2 in ('id', 'section', 'text', 'previous_sentence', 'cited', 'flags')}, ensure_ascii=False)}"]
            for p in c["papers"]:
                parts.append(f"ROW of cited paper [{p['n']}] ({p['row_file']}):\n{json.dumps(rows_all[Path(p['row_file']).stem], ensure_ascii=False)}")
            if len(c["cited"]) == 0 or len(c["cited"]) >= 5:
                for name in ("table.md", "PRISMA.md", "selection.txt"):
                    if name in extra and (name == "table.md" or not c["cited"]):
                        parts.append(f"{name}:\n{extra[name]}")
            user = "\n\n".join(parts)
            if len(user) > cfg.max_prompt_chars:
                return c["id"], None, [f"prompt too long ({len(user)} chars)"]

            def validate(r):
                if not isinstance(r, dict) or r.get("verdict") not in CLAIM_VERDICTS or not isinstance(r.get("wrong_citation"), bool):
                    return ['need {"id", "verdict": SUPPORTED|PARTIAL|UNSUPPORTED|NOT-CHECKABLE, "wrong_citation": true/false, "issue": "..."}'], []
                return [], []

            obj, probs = ask(cfg, "claim_check", str(c["id"]), system, user, validate, log)
            if obj is not None:
                obj["id"] = c["id"]
            return c["id"], obj, probs

        res = run_pool(cfg, claims, work, "claim")
        all_res += res
        ok = {i: o for i, o, _ in res if o}
        if len(ok) == len(claims) and not cfg.only:
            target.write_text(json.dumps([ok[c["id"]] for c in claims], indent=1, ensure_ascii=False), encoding="utf-8")
        else:
            print(f"{target.name} NOT written: {len(ok)} of {len(claims)} claims have a valid reply")
    return all_res


def run_pool(cfg, items, work, label):
    res = []
    with cf.ThreadPoolExecutor(max_workers=cfg.workers) as ex:
        for r in ex.map(work, items):
            res.append(r)
            tag = "ok" if r[1] is not None and not r[2] else ("ok with notes" if r[1] is not None else "FAILED")
            print(f"  {label} {r[0]}: {tag}" + (f" ({'; '.join(r[2])[:150]})" if r[2] else ""))
    return res


STEPS = {"extract_row": step_extract_row, "atomic_claims": step_atomic_claims, "audit_cells": step_audit_cells,
         "claim_check": step_claim_check}


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=STEPS)
    ap.add_argument("run_dir")
    ap.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL", "http://localhost:8000/v1"))
    ap.add_argument("--model", default=os.environ.get("LLM_MODEL", ""))
    ap.add_argument("--api-key-env", default="LLM_API_KEY")
    ap.add_argument("--out-dir")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--group")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--max-tokens", type=int, default=2048)
    ap.add_argument("--json-mode", action="store_true")
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--max-prompt-chars", type=int, default=120000)
    ap.add_argument("--prisma")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    cfg = ap.parse_args(argv)
    run = Path(cfg.run_dir)
    system = to_api(cfg.step, (run / "prompts" / f"{cfg.step}.md").read_text(encoding="utf-8"))
    if cfg.dry_run:
        print("=== SYSTEM ===\n" + system)
        first = next(iter(sorted((run / "packets").glob("*.md"))), None) if cfg.step == "extract_row" else None
        print("=== USER (first item) ===\n" + (first.read_text(encoding="utf-8")[:1500] + "\n[...]" if first else "(built per item)"))
        return 0
    if not cfg.model:
        raise SystemExit("no model name: pass --model or set LLM_MODEL")
    logf = Path(cfg.out_dir or run)
    logf.mkdir(parents=True, exist_ok=True)
    logp = logf / "llm_log.jsonl"
    lock = threading.Lock()

    def log(rec):
        rec.update(ts=time.strftime("%Y-%m-%dT%H:%M:%S"), model=cfg.model, base_url=cfg.base_url)
        with lock, open(logp, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    res = STEPS[cfg.step](cfg, run, system, log)
    failed = [r for r in res if r[1] is None]
    print(f"{cfg.step}: {len(res)} items, {len(failed)} failed; log: {logp}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]) if len(sys.argv) >= 3 else print(__doc__) or 2)
