#!/usr/bin/env python3
"""Prepare the inputs of the two sub-agent steps and render their prompts.

  python -I -X utf8 tools/prep_agents.py groups RUN_DIR [N_GROUPS=6]
      packets/*.md ids, sorted, split into N consecutive groups -> RUN_DIR/g1.txt ... gN.txt
  python -I -X utf8 tools/prep_agents.py audit RUN_DIR [N_PAPERS=12] [SEED=0] [IDS_FILE]
      random N papers x 2 fields (control_mechanism, controllability_evidence) from rows/*.json
      -> RUN_DIR/audit_cells.json   (the sample is a function of SEED; record it)
  python -I -X utf8 tools/prep_agents.py render TEMPLATE RUN_DIR [GROUP_FILE]
      prints a prompt template from RUN_DIR/prompts with {RUN_DIR}, {GROUP_FILE}, {N_CELLS} filled in

The templates are the exact prompts used for the 34-row table (the group number was the only thing that changed).
"""
import json
import random
import sys
from pathlib import Path

AUDIT_FIELDS = ("control_mechanism", "controllability_evidence")


def groups(run: Path, n: int) -> None:
    ids = sorted(p.stem for p in (run / "packets").glob("*.md"))
    k, r = divmod(len(ids), n)
    i = 0
    for g in range(n):
        size = k + (1 if g < r else 0)
        (run / f"g{g + 1}.txt").write_text("\n".join(ids[i:i + size]) + "\n", encoding="utf-8")
        i += size
    print(f"{len(ids)} ids in {n} groups")


def audit(run: Path, n: int, seed: int, only: str = "") -> None:
    rows = sorted((run / "rows").glob("*.json"))
    if only:  # sample only from the ids listed in this file (for example the rows added in a later round)
        keep = {x.strip() for x in open(only, encoding="utf-8") if x.strip()}
        rows = [f for f in rows if f.stem in keep]
    pick = random.Random(seed).sample(rows, n)
    cells = []
    for f in pick:
        r = json.loads(f.read_text(encoding="utf-8"))
        for fld in AUDIT_FIELDS:
            v = r[fld]
            cells.append({"packet": f"packets/{f.stem}.md", "field": fld,
                          "claimed_value": v["value"], "claimed_pages": v["pages"]})
    (run / "audit_cells.json").write_text(json.dumps(cells, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(cells)} cells from {n} papers, seed {seed}")


def render(run: Path, template: str, group_file: str) -> None:
    t = (run / "prompts" / f"{template}.md").read_text(encoding="utf-8")
    n_cells = len(json.loads((run / "audit_cells.json").read_text(encoding="utf-8"))) if (run / "audit_cells.json").is_file() else "N"
    gp = Path(group_file)  # claim_check: chunk file claims_K.json -> result file claims_result_K.json in the same folder
    result = str(gp.with_name(gp.name.replace("claims_", "claims_result_", 1)))
    print(t.replace("{RUN_DIR}", str(run.resolve())).replace("{GROUP_FILE}", group_file)
          .replace("{RESULT_FILE}", result).replace("{N_CELLS}", str(n_cells)))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "groups":
        groups(Path(a[1]), int(a[2]) if len(a) > 2 else 6)
    elif len(a) >= 2 and a[0] == "audit":
        audit(Path(a[1]), int(a[2]) if len(a) > 2 else 12, int(a[3]) if len(a) > 3 else 0, a[4] if len(a) > 4 else "")
    elif len(a) >= 3 and a[0] == "render":
        render(Path(a[2]), a[1], a[3] if len(a) > 3 else "{GROUP_FILE}")
    else:
        print(__doc__)
        raise SystemExit(2)
