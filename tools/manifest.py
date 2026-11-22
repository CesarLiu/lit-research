#!/usr/bin/env python3
"""Provenance manifest: what produced each output of a run, and has it changed since.

  python -I -X utf8 tools/manifest.py run    RUN_DIR --step NAME [--inputs P ...] [--outputs P ...] [--shallow P ...]
                                             [--deterministic] [--model TEXT] [--note TEXT] -- COMMAND ...
  python -I -X utf8 tools/manifest.py record RUN_DIR --step NAME --cmd TEXT [same options] [--backfilled]
  python -I -X utf8 tools/manifest.py verify RUN_DIR
  python -I -X utf8 tools/manifest.py show   RUN_DIR

run      executes COMMAND from the current folder (the project root) and, only if it exits 0, appends a record.
record   appends a record without running anything: for steps done by sub-agents or by hand, or to backfill.
verify   re-hashes what the latest record of each output says and reports OK, CHANGED, MISSING, and records whose
         inputs have changed since (the output may be stale). It does NOT re-run commands: it shows that files are
         unchanged since recorded, not that a command would reproduce them.
show     one line per record.

Records go to RUN_DIR/MANIFEST.jsonl, one JSON object per line: time, step, command, input and output hashes
(SHA-256; a folder is hashed from its files' names and hashes), git commit and whether tools/ had uncommitted
changes, Python version, whether the step is deterministic, the model (text you give; if an llm_log.jsonl is found
among the outputs or in RUN_DIR, its models and request count), and a note. Paths are relative to the current folder.
  --shallow  paths recorded as file count and total bytes only (for big folders such as downloaded PDFs)
  deterministic=true means the same inputs and code give the same bytes (search merging, table assembly); model steps,
  live web or API fetches, and files with embedded timestamps (pptx, pdf) are not.
"""
import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from pathlib import Path


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def files_of(p: Path):
    return sorted(f for f in p.rglob("*") if f.is_file() and "__pycache__" not in f.parts)


def digest(p: str, shallow: bool = False) -> str:
    """'sha256:..' for a file, 'dir:<n files>:<hash>' for a folder, 'shallow:<n files>:<bytes>', or 'missing'."""
    path = Path(p)
    if not path.exists():
        return "missing"
    if path.is_file():
        return "sha256:" + sha(path)
    fs = files_of(path)
    if shallow:
        return f"shallow:{len(fs)}:{sum(f.stat().st_size for f in fs)}"
    h = hashlib.sha256()
    for f in fs:
        h.update(f"{f.relative_to(path).as_posix()}\0{sha(f)}\n".encode())
    return f"dir:{len(fs)}:{h.hexdigest()}"


def git_info() -> dict:
    def g(*a):
        try:
            return subprocess.run(["git", *a], capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception:  # noqa: BLE001
            return ""
    return {"commit": g("rev-parse", "HEAD") or None, "tools_dirty": bool(g("status", "--porcelain", "--", "tools"))}


def llm_info(run: Path, outputs: list[str]) -> dict | None:
    cands = [Path(o).parent / "llm_log.jsonl" for o in outputs] + [run / "llm_log.jsonl"]
    for c in cands:
        if c.is_file():
            recs = [json.loads(x) for x in c.read_text(encoding="utf-8").splitlines() if x.strip()]
            return {"log": c.as_posix(), "models": sorted({r.get("model", "?") for r in recs}), "requests": len(recs)}
    return None


def make_record(a, cmd_text: str) -> dict:
    shallow = set(a.shallow or [])
    return {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "step": a.step, "cmd": cmd_text,
        "inputs": {p: digest(p, p in shallow) for p in (a.inputs or [])},
        "outputs": {p: digest(p, p in shallow) for p in (a.outputs or []) + (a.shallow or [])},
        "shallow": sorted(shallow),
        "deterministic": bool(a.deterministic), "model": a.model, "llm": llm_info(Path(a.run_dir), (a.outputs or [])),
        "git": git_info(), "python": platform.python_version(), "backfilled": bool(getattr(a, "backfilled", False)),
        "note": a.note,
    }


def append(run_dir: str, rec: dict) -> None:
    Path(run_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(run_dir) / "MANIFEST.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def load(run_dir: str) -> list[dict]:
    f = Path(run_dir) / "MANIFEST.jsonl"
    if not f.is_file():
        raise SystemExit(f"no {f}")
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def verify(run_dir: str) -> int:
    recs = load(run_dir)
    latest = {}  # output path -> index of the latest record that lists it
    for i, r in enumerate(recs):
        for p in r["outputs"]:
            latest[p] = i
    bad = 0
    for i, r in enumerate(recs):
        shallow = set(r.get("shallow", []))
        lines = []
        for p, old in r["outputs"].items():
            if latest[p] != i:
                continue  # a later record owns this output
            now = digest(p, p in shallow)
            if now == "missing":
                lines.append(f"    MISSING  {p}")
            elif now != old:
                lines.append(f"    CHANGED  {p}")
        stale = [p for p, old in r["inputs"].items() if digest(p, p in shallow) != old]
        if stale:
            lines.append(f"    INPUTS CHANGED since this step ran (output may be stale): {', '.join(stale)}")
        flag = " [backfilled]" if r.get("backfilled") else ""
        print(f"{r['ts']}  {r['step']}{flag}: " + ("OK" if not lines else "PROBLEMS"))
        for ln in lines:
            print(ln)
            bad += 1
    print(f"{len(recs)} records, {bad} problem line(s). Hashes show files unchanged since recorded; they do not re-run anything.")
    return 1 if bad else 0


def show(run_dir: str) -> int:
    for r in load(run_dir):
        mdl = " / ".join(str(x) for x in (r.get("model"), r["llm"]["models"] if r.get("llm") else None) if x)
        print(f"{r['ts']}  {r['step']:<22} det={'y' if r['deterministic'] else 'n'}  model={mdl}  "
              f"git={str(r['git']['commit'])[:7]}{'*' if r['git']['tools_dirty'] else ''}{'  backfilled' if r.get('backfilled') else ''}")
        print(f"    {r['cmd'][:150]}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)

    def common(p):
        p.add_argument("run_dir")
        p.add_argument("--step", required=True)
        p.add_argument("--inputs", nargs="*")
        p.add_argument("--outputs", nargs="*")
        p.add_argument("--shallow", nargs="*")
        p.add_argument("--deterministic", action="store_true")
        p.add_argument("--model")
        p.add_argument("--note")

    r = sub.add_parser("run")
    common(r)
    c = sub.add_parser("record")
    common(c)
    c.add_argument("--cmd", required=True)
    c.add_argument("--backfilled", action="store_true")
    for name in ("verify", "show"):
        sub.add_parser(name).add_argument("run_dir")
    command: list[str] = []
    if "--" in argv:  # everything after the first -- is the command to run
        i = argv.index("--")
        argv, command = argv[:i], argv[i + 1:]
    a = ap.parse_args(argv)
    if a.mode == "verify":
        return verify(a.run_dir)
    if a.mode == "show":
        return show(a.run_dir)
    if a.mode == "run":
        cmd = command
        if not cmd:
            raise SystemExit("run: give the command after --")
        code = subprocess.run(cmd).returncode
        if code != 0:
            print(f"command exited {code}: no record written", file=sys.stderr)
            return code
        append(a.run_dir, make_record(a, " ".join(cmd)))
    else:
        append(a.run_dir, make_record(a, a.cmd))
    print(f"recorded step {a.step} in {Path(a.run_dir) / 'MANIFEST.jsonl'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]) if len(sys.argv) > 1 else print(__doc__) or 2)
