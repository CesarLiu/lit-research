#!/usr/bin/env python3
"""Split a review into checkable claims and attach the table rows each claim cites.

  python -I -X utf8 tools/split_claims.py REVIEW.md REFS.json ROWS_DIR OUT_DIR [N_CHUNKS=4] [--industry ROWS.json]

--industry: company statements (runs/industry/rows.json). A sentence citing [W1], [N8] and so on gets those statements
(company, date, claim, verbatim quote, grade) attached as "company_statements", and its numbers are checked against them.

Units: sentences of paragraphs and list items, and whole table rows, in the numbered sections before "Validity".
Headings, the reference list and the Validity section are skipped (Validity describes the process, which is
checked elsewhere). Each unit gets: the cited reference numbers [n], the row file of each, and deterministic flags:
  number_not_in_cited_rows  a number in the sentence occurs in none of the cited rows (all rows if nothing is cited)
  no_citation               the sentence cites nothing but contains a digit or a number word (a count or a claim
                            that the table must support)
Writes OUT_DIR/claims_1.json ... claims_N.json (so they can go to separate checkers) and OUT_DIR/claims_flags.txt.
The flags only prioritise; the judging is done by the checker (see prompts/claim_check.md).
"""
import json
import re
import sys
from pathlib import Path

CITE = re.compile(r"\[(\d+)\]")
NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
NUMWORD = re.compile(r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|all|none|most|half)\b", re.I)
SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\[\*(])")
PROTECT = ["e.g.", "i.e.", "et al.", "vs.", "approx."]


def split_sentences(par: str) -> list[str]:
    for i, p in enumerate(PROTECT):
        par = par.replace(p, f"\x00{i}\x00")
    out = SPLIT.split(par)
    res = []
    for s in out:
        for i, p in enumerate(PROTECT):
            s = s.replace(f"\x00{i}\x00", p)
        if s.strip():
            res.append(s.strip())
    return res


def units(md: str):
    section = ""
    par = []

    def flush():
        nonlocal par
        if par:
            text = " ".join(par)
            par = []
            for s in split_sentences(text):
                yield section, s

    for ln in md.splitlines():
        if ln.startswith("#"):
            yield from flush()
            section = ln.lstrip("# ").strip()
            continue
        if re.sub(r"^[\d.\s]+", "", section).lower().startswith(("validity", "references")):
            continue
        if ln.startswith("|"):
            yield from flush()
            if set(ln.replace("|", "").strip()) <= set("-: ") or ln.lower().startswith("| family"):
                continue
            yield section, "TABLE ROW: " + " | ".join(c.strip() for c in ln.strip().strip("|").split("|"))
        elif not ln.strip():
            yield from flush()
        elif re.match(r"^(- |\d+\.\s)", ln):  # a list item starts a new unit
            yield from flush()
            par.append(re.sub(r"^(- |\d+\.\s)", "", ln).strip())
        elif ln.startswith("*Built only from"):
            continue
        else:
            par.append(ln.strip())
    yield from flush()


CITE_CO = re.compile(r"\[([A-Z]\d+)\]")  # company statement codes such as [W1], see --industry


def main(review: str, refs: str, rows_dir: str, out: str, n_chunks: int = 4, industry: str = "") -> int:
    R = {r["n"]: r for r in json.loads(Path(refs).read_text(encoding="utf-8"))}
    rows = {p.stem: p.read_text(encoding="utf-8") for p in Path(rows_dir).glob("*.json")}
    all_text = " ".join(rows.values())
    co = {r["id"]: r for r in json.loads(Path(industry).read_text(encoding="utf-8"))} if industry else {}
    outd = Path(out)
    outd.mkdir(parents=True, exist_ok=True)
    claims, flags = [], []
    for i, (sec, text) in enumerate(units(Path(review).read_text(encoding="utf-8")), 1):
        cited = sorted({int(x) for x in CITE.findall(text)})
        co_ids = sorted({x for x in CITE_CO.findall(text) if x in co})
        unknown = [n for n in cited if n not in R] + [x for x in CITE_CO.findall(text) if x not in co]
        body = CITE_CO.sub(" ", CITE.sub(" ", text))
        nums = sorted(set(NUM.findall(re.sub(r"^\d+\.\s", "", body))))
        src = " ".join(rows.get(R[n]["id"], "") for n in cited if n in R)
        src += " " + " ".join(co[x]["quote"] + " " + co[x]["claim"] for x in co_ids)
        if not cited and not co_ids:
            src = all_text
        fl = []
        if unknown:
            fl.append(f"unknown_ref {unknown}")
        for n in nums:
            if n not in src and n.rstrip("0").rstrip(".") not in src:
                fl.append(f"number_not_in_cited_rows {n}")
        if not cited and not co_ids and (NUM.search(body) or NUMWORD.search(body)):
            fl.append("no_citation")
        claims.append({"id": i, "section": sec, "text": text, "cited": cited,
                       "company_statements": [{k: co[x][k] for k in ("id", "company", "date", "claim", "quote", "grade", "page")}
                                              for x in co_ids],
                       "previous_sentence": claims[-1]["text"] if claims and claims[-1]["section"] == sec else "",
                       "papers": [{"n": n, "row_file": f"rows/{R[n]['id']}.json", "title": R[n]["title"]} for n in cited if n in R],
                       "flags": fl})
        if fl:
            flags.append(f"{i:3d} [{sec[:28]}] {'; '.join(fl)} :: {text[:90]}")
    size = -(-len(claims) // n_chunks)
    for k in range(n_chunks):
        (outd / f"claims_{k + 1}.json").write_text(
            json.dumps(claims[k * size:(k + 1) * size], indent=1, ensure_ascii=False), encoding="utf-8")
    (outd / "claims_flags.txt").write_text("\n".join(flags) + "\n", encoding="utf-8")
    print(f"{len(claims)} claims in {n_chunks} chunks; {len(flags)} with flags ({sum('number_not' in f for f in flags)} number, "
          f"{sum('no_citation' in f for f in flags)} uncited)")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    ind = a[a.index("--industry") + 1] if "--industry" in a else ""
    a = [x for i, x in enumerate(a) if x != "--industry" and (i == 0 or a[i - 1] != "--industry")]
    raise SystemExit(main(a[0], a[1], a[2], a[3], int(a[4]) if len(a) > 4 else 4, ind) if len(a) >= 4 else print(__doc__) or 2)
