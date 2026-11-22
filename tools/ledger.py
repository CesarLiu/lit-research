#!/usr/bin/env python3
"""Atomic-claim ledger: one row per checkable number a paper reports, and the record of whether it was reproduced.

  python -I -X utf8 tools/ledger.py check-extract RUN_DIR      validate atomic/<id>.json against the evidence packets
  python -I -X utf8 tools/ledger.py audit-cells RUN_DIR OUT_DIR  one audit cell per claim, for an independent audit
  python -I -X utf8 tools/ledger.py build RUN_DIR [--force]    atomic/*.json + refs.json + packets -> RUN_DIR/ledger.csv
  python -I -X utf8 tools/ledger.py check RUN_DIR              rules on the ledger (statuses, registration, results)
  python -I -X utf8 tools/ledger.py register RUN_DIR CLAIM_ID --tolerance abs:0.5|rel:0.05 --budget TEXT --approved-by NAME
                                           [--mapping-checked NAME]
  python -I -X utf8 tools/ledger.py result RUN_DIR CLAIM_ID --status reproduced|partial|not_reproduced|blocked
                                           --observed NUMBER --run-ref PATH [--note TEXT]

Run from the project root (git is asked for the committed copy of the ledger).

Extraction (a model step, prompt prompts/atomic_claims.md) writes RUN_DIR/atomic/<paper id>.json = {"id", "claims": [..]}.
check_claims() below is the deterministic check of such a file: every quote must occur in the paper's evidence packet,
every number must occur in the packet, one number per claim is expected.

Order of use for a claim: build -> register (sets tolerance, budget and who approved; status 'registered') -> COMMIT the
ledger -> run the experiment elsewhere -> result. `result` refuses unless the committed ledger already holds the same
tolerance, budget, approver and registration time for that claim, so the pass criterion cannot be set after seeing the
number. It refuses 'reproduced' when the observed number is outside the tolerance. The approval is whatever name you
pass to --approved-by; this tool cannot tell whether a person really approved. `code_url` is only a link found in the
evidence packet (a lower bound, and a link on a later page may be another paper's code); it is not checked to work.
"""
import csv
import json
import re
import subprocess
import sys
import time
from pathlib import Path

KINDS = {"control_effect", "main_result", "ablation"}
CLAIM_FIELDS = ["claim", "kind", "metric", "condition", "reported_value", "comparison", "quote", "page"]
COLS = ["claim_id", "paper_n", "paper", "kind", "claim", "metric", "condition", "reported_value", "comparison", "quote", "page",
        "code_url", "code_link_where", "status", "tolerance", "budget", "approved_by", "registered_at", "observed",
        "observed_at", "run_ref", "note"]
STATUSES = {"not_attempted", "registered", "reproduced", "partial", "not_reproduced", "blocked"}
DONE = {"reproduced", "partial", "not_reproduced"}
NUM = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?")
CODE = re.compile(r"(?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co)/[A-Za-z0-9_.\-]+(?:/[A-Za-z0-9_.\-]+)?", re.I)
PM = re.compile(r"\s*(?:±|\+/-|\+-)\s*\d+(?:\.\d+)?")  # "5.8 +/- 0.4": the spread is not a second value
MAX_CLAIMS = 6
FRAG = "MAPPING UNVERIFIED (table fragment)."


def main_values(s: str) -> list[str]:
    """Numbers of a reported value without the spread that follows a plus-minus sign."""
    return NUM.findall(PM.sub("", s))


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def check_claims(pid: str, obj, ptxt: str) -> tuple[list[str], list[str]]:
    """(hard problems, soft problems) of one extraction file against its evidence packet text."""
    if not isinstance(obj, dict) or not isinstance(obj.get("claims"), list):
        return ['reply must be {"claims": [ ... ]}'], []
    hard, soft = [], []
    claims = obj["claims"]
    if len(claims) > MAX_CLAIMS:
        soft.append(f"{pid}: {len(claims)} claims, at most {MAX_CLAIMS} wanted")
    sq = squash(ptxt)
    for i, c in enumerate(claims, 1):
        tag = f"{pid} claim {i}"
        if not isinstance(c, dict):
            hard.append(f"{tag}: not an object")
            continue
        bad = [f for f in CLAIM_FIELDS if not isinstance(c.get(f), str)]
        if bad:
            hard.append(f"{tag}: missing or non-text fields {bad}")
            continue
        if c["kind"] not in KINDS:
            hard.append(f"{tag}: kind {c['kind']!r} not one of {sorted(KINDS)}")
        if not c["page"].strip():
            hard.append(f"{tag}: no page")
        q = c["quote"]
        if not q.strip() or squash(q) not in sq:
            hard.append(f"{tag}: quote is not verbatim in the packet: {q[:60]!r}")
        if len(q.split()) > 30:
            soft.append(f"{tag}: quote longer than 30 words")
        nums = NUM.findall(c["reported_value"])
        if not nums:
            hard.append(f"{tag}: reported_value has no number")
        for n in nums:
            if n not in ptxt:
                hard.append(f"{tag}: number {n} is not in the packet")
            elif n not in q:
                soft.append(f"{tag}: number {n} is in the packet but not in the quote")
        if len(NUM.findall(q)) >= 4:
            soft.append(f"{tag}: the quote holds {len(NUM.findall(q))} numbers, so it is a table fragment: which row and column "
                        "the value belongs to is a guess until a person checks the packet or the paper")
        if len(main_values(c["reported_value"])) > 1:
            soft.append(f"{tag}: more than one number in reported_value; one value per claim is wanted")
    return hard, soft


def read_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_check_extract(run: Path) -> int:
    bad = 0
    files = sorted((run / "atomic").glob("*.json"))
    for f in files:
        ptxt = (run / "packets" / f"{f.stem}.md")
        if not ptxt.is_file():
            print(f"{f.stem}: no packet")
            bad += 1
            continue
        try:
            obj = read_json(f)
        except ValueError as e:
            print(f"{f.stem}: invalid JSON ({e})")
            bad += 1
            continue
        hard, soft = check_claims(f.stem, obj, ptxt.read_text(encoding="utf-8"))
        for p in hard:
            print("HARD", p)
        for p in soft:
            print("soft", p)
        bad += len(hard)
    print(f"{len(files)} extraction files, {bad} hard problem(s)")
    return 1 if bad else 0


def code_link(ptxt: str) -> tuple[str, str]:
    first = ptxt.split("## Passages")[0]
    for where, text in (("first pages", first), ("later in packet only", ptxt)):
        m = CODE.search(text)
        if m:
            return m.group(0).rstrip(".,);"), where
    return "", ""


def cmd_build(run: Path, force: bool) -> int:
    out = run / "ledger.csv"
    if out.exists() and not force:
        raise SystemExit(f"{out} exists; rebuilding would erase registrations and results. Use --force if you mean it")
    refs = {r["id"]: r for r in read_json(run / "refs.json")}
    rows = []
    for f in sorted((run / "atomic").glob("*.json")):
        ref = refs.get(f.stem)
        if not ref:
            print(f"{f.stem}: not in refs.json, skipped")
            continue
        url, where = code_link((run / "packets" / f"{f.stem}.md").read_text(encoding="utf-8"))
        for k, c in enumerate(read_json(f)["claims"], 1):
            rows.append({"claim_id": f"P{ref['n']:02d}-C{k}", "paper_n": ref["n"], "paper": ref["short"], **{x: c[x] for x in CLAIM_FIELDS},
                         "code_url": url, "code_link_where": where, "status": "not_attempted", "tolerance": "", "budget": "",
                         "approved_by": "", "registered_at": "", "observed": "", "observed_at": "", "run_ref": "",
                         "note": FRAG if len(NUM.findall(c["quote"])) >= 4 else ""})
    rows.sort(key=lambda r: (int(r["paper_n"]), r["claim_id"]))
    write(out, rows)
    print(f"{len(rows)} claims from {len({r['paper_n'] for r in rows})} papers -> {out}")
    return 0


def read_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, COLS)
        w.writeheader()
        w.writerows(rows)


def parse_tol(t: str):
    m = re.fullmatch(r"(abs|rel):(\d+(?:\.\d+)?)", t.strip())
    if not m or float(m.group(2)) <= 0:
        raise SystemExit("tolerance must look like abs:0.5 or rel:0.05 (a positive number)")
    return m.group(1), float(m.group(2))


def within(kind: str, tol: float, reported: float, observed: float) -> bool:
    return abs(observed - reported) <= (tol if kind == "abs" else tol * abs(reported))


def cmd_check(run: Path) -> int:
    rows = read_rows(run / "ledger.csv")
    bad, ids = [], set()
    for r in rows:
        cid, st = r["claim_id"], r["status"]
        if cid in ids:
            bad.append(f"{cid}: duplicate id")
        ids.add(cid)
        if st not in STATUSES:
            bad.append(f"{cid}: status {st!r} not allowed")
            continue
        if st != "not_attempted":
            for f in ("tolerance", "budget", "approved_by", "registered_at"):
                if not r[f].strip():
                    bad.append(f"{cid}: status {st} but {f} is empty (registration comes before running)")
            try:
                parse_tol(r["tolerance"])
            except SystemExit as e:
                bad.append(f"{cid}: {e}")
        if st in DONE:
            for f in ("observed", "observed_at", "run_ref"):
                if not r[f].strip():
                    bad.append(f"{cid}: status {st} but {f} is empty")
            if r["observed_at"] and r["registered_at"] and r["observed_at"] < r["registered_at"]:
                bad.append(f"{cid}: observed_at is before registered_at")
            if st == "reproduced":
                try:
                    k, t = parse_tol(r["tolerance"])
                    rep, obs = main_values(r["reported_value"]), float(r["observed"])
                    if len(rep) != 1:
                        bad.append(f"{cid}: reproduced needs exactly one reported number to compare, found {len(rep)}")
                    elif not within(k, t, float(rep[0]), obs):
                        bad.append(f"{cid}: marked reproduced but {obs} is outside {r['tolerance']} of {rep[0]}")
                except (SystemExit, ValueError):
                    pass
        if st == "registered" and (r["observed"] or r["observed_at"]):
            bad.append(f"{cid}: has an observed value but status is still registered")
        if st == "not_attempted" and (r["observed"] or r["tolerance"] or r["approved_by"]):
            bad.append(f"{cid}: status not_attempted but registration or result fields are filled")
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    withcode = len({r["paper_n"] for r in rows if r["code_url"]})
    print(f"{len(rows)} claims from {len({r['paper_n'] for r in rows})} papers ({withcode} with a code link in the packet); "
          + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    print("\n".join(bad) if bad else "no problems found")
    return 1 if bad else 0


def committed_row(path: Path, cid: str):
    r = subprocess.run(["git", "show", f"HEAD:./{path.as_posix()}"], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    import io
    return next((x for x in csv.DictReader(io.StringIO(r.stdout)) if x["claim_id"] == cid), None)


def find(rows, cid):
    hit = [r for r in rows if r["claim_id"] == cid]
    if not hit:
        raise SystemExit(f"no claim {cid}")
    return hit[0]


def cmd_register(run: Path, cid: str, tol: str, budget: str, who: str, mapping_checked: str) -> int:
    parse_tol(tol)
    if not budget.strip() or not who.strip():
        raise SystemExit("--budget and --approved-by must not be empty")
    path = run / "ledger.csv"
    rows = read_rows(path)
    r = find(rows, cid)
    if r["status"] != "not_attempted":
        raise SystemExit(f"{cid} is already {r['status']}; a registration is not changed after it is made")
    if r["note"].startswith(FRAG):
        if not mapping_checked.strip():
            raise SystemExit(f"{cid}: {FRAG} Check the packet or the paper, then pass --mapping-checked YOUR_NAME")
        r["note"] = f"Mapping checked by {mapping_checked.strip()}. " + r["note"][len(FRAG):].strip()
    r.update(status="registered", tolerance=tol.strip(), budget=budget.strip(), approved_by=who.strip(),
             registered_at=time.strftime("%Y-%m-%dT%H:%M:%S"))
    write(path, rows)
    print(f"{cid} registered with tolerance {tol}; commit {path.as_posix()} before running the experiment")
    return 0


def cmd_result(run: Path, cid: str, status: str, observed: str, run_ref: str, note: str) -> int:
    path = run / "ledger.csv"
    rows = read_rows(path)
    r = find(rows, cid)
    if status not in DONE | {"blocked"}:
        raise SystemExit("status must be reproduced, partial, not_reproduced or blocked")
    if r["status"] != "registered":
        raise SystemExit(f"{cid} is {r['status']}; register it first")
    old = committed_row(path, cid)
    keys = ("status", "tolerance", "budget", "approved_by", "registered_at")
    if old is None or any(old[k] != r[k] for k in keys):
        raise SystemExit(f"the committed ledger does not hold this registration of {cid}: commit {path.as_posix()} "
                         "after registering and before recording a result")
    try:
        obs = float(observed)
    except ValueError:
        raise SystemExit("--observed must be a number") from None
    if status == "reproduced":
        rep = main_values(r["reported_value"])
        if len(rep) != 1:
            raise SystemExit(f"cannot mark reproduced: reported_value has {len(rep)} numbers; use partial and explain in --note")
        k, t = parse_tol(r["tolerance"])
        if not within(k, t, float(rep[0]), obs):
            raise SystemExit(f"{obs} is outside {r['tolerance']} of the reported {rep[0]}: use partial or not_reproduced")
    r.update(status=status, observed=observed.strip(), observed_at=time.strftime("%Y-%m-%dT%H:%M:%S"), run_ref=run_ref,
             note=(r["note"] + " " + note).strip())
    write(path, rows)
    print(f"{cid}: {status}, observed {observed}")
    return 0


def cmd_audit_cells(run: Path, out: Path) -> int:
    """One audit cell per extracted claim, for the audit prompt (prompts/audit_cells.md) run with OUT_DIR as RUN_DIR."""
    cells = []
    for f in sorted((run / "atomic").glob("*.json")):
        for c in read_json(f)["claims"]:
            cells.append({"packet": f"../packets/{f.stem}.md", "field": "atomic_claim",
                          "claimed_value": f"{c['claim']} | metric: {c['metric']} | condition: {c['condition']} | value: "
                                           f"{c['reported_value']} | compared with: {c['comparison']}",
                          "claimed_pages": c["page"]})
    out.mkdir(parents=True, exist_ok=True)
    (out / "audit_cells.json").write_text(json.dumps(cells, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cells)} cells -> {out / 'audit_cells.json'}")
    return 0


def main(a: list[str]) -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    for n in ("check-extract", "check"):
        sub.add_parser(n).add_argument("run_dir")
    q = sub.add_parser("audit-cells")
    q.add_argument("run_dir")
    q.add_argument("out_dir")
    b = sub.add_parser("build")
    b.add_argument("run_dir")
    b.add_argument("--force", action="store_true")
    g = sub.add_parser("register")
    g.add_argument("run_dir")
    g.add_argument("claim_id")
    g.add_argument("--tolerance", required=True)
    g.add_argument("--budget", required=True)
    g.add_argument("--approved-by", required=True)
    g.add_argument("--mapping-checked", default="")
    s = sub.add_parser("result")
    s.add_argument("run_dir")
    s.add_argument("claim_id")
    s.add_argument("--status", required=True)
    s.add_argument("--observed", required=True)
    s.add_argument("--run-ref", required=True)
    s.add_argument("--note", default="")
    x = ap.parse_args(a)
    run = Path(x.run_dir)
    if x.mode == "check-extract":
        return cmd_check_extract(run)
    if x.mode == "audit-cells":
        return cmd_audit_cells(run, Path(x.out_dir))
    if x.mode == "build":
        return cmd_build(run, x.force)
    if x.mode == "check":
        return cmd_check(run)
    if x.mode == "register":
        return cmd_register(run, x.claim_id, x.tolerance, x.budget, x.approved_by, x.mapping_checked)
    return cmd_result(run, x.claim_id, x.status, x.observed, x.run_ref, x.note)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]) if len(sys.argv) > 1 else print(__doc__) or 2)
