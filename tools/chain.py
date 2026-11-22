#!/usr/bin/env python3
"""Citation chaining with OpenAlex, from a set of seed papers.

  python -I -X utf8 tools/chain.py RESULTS.json SELECTION.txt OUT_DIR [--min-seeds 2] [--cap 400]

Seeds: the papers named in SELECTION.txt (title substring, optional " # reason"), looked up in RESULTS.json.
Backward: works the seeds cite. Forward: works that cite the seeds. A candidate is kept when it is linked to at
least --min-seeds different seeds (one link is mostly noise). Each candidate is marked:
  in_corpus   already in RESULTS.json (by OpenAlex id, DOI or normalised title)
  in_window   published 2019 or later (the window of the original search)
  on_topic    passes the same DRIVE and TASK keyword rule as merge_results.py (title plus abstract when OpenAlex
              has one; backward candidates often have only a title, so this is weaker for them)
Writes OUT_DIR/chain_candidates.csv (sorted by number of seeds) and OUT_DIR/chain_summary.txt. Raw API replies are
cached in OUT_DIR/cache so a rerun costs no requests. No credentials or e-mail are sent.
Candidates are leads: a person or the screening step decides whether they enter the review.
"""
import csv
import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merge_results import DRIVE, TASK  # noqa: E402

API = "https://api.openalex.org/works"
SEL = "id,doi,title,publication_year,cited_by_count,abstract_inverted_index"


# stricter rule for ranking the leads: names the task (scenario / simulation / adversarial) AND a generative or control word
TIGHT_A = re.compile(r"\b(scenario\w*|traffic simulation|driving simulation|sim agents?|safety-critical|traffic generation|scene generation|simulat\w*)\b", re.I)
TIGHT_B = re.compile(r"\b(generat\w*|diffusion|controllab\w*|adversar\w*|synthes\w*|steer\w*|conditional)\b", re.I)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def abstract(inv) -> str:
    if not inv:
        return ""
    pos = {p: w for w, ps in inv.items() for p in ps}
    return " ".join(pos[i] for i in sorted(pos))


class Client:
    def __init__(self, cache: Path):
        self.cache = cache
        cache.mkdir(parents=True, exist_ok=True)
        self.n = 0

    def get(self, url: str) -> dict:
        f = self.cache / (hashlib.sha1(url.encode()).hexdigest() + ".json")
        if f.is_file():
            return json.loads(f.read_text(encoding="utf-8"))
        for attempt in range(4):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "lit-chain/1.0"})
                with urllib.request.urlopen(req, timeout=40) as r:
                    data = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if e.code in (401, 402, 403):  # budget or key problem: retrying will not help
                    raise SystemExit(f"HTTP {e.code} from OpenAlex: {e.read()[:300]!r}\nurl: {url}\n"
                                     f"{self.n} requests made; cached replies are kept, rerun after fixing")
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
            except Exception:  # noqa: BLE001
                if attempt == 3:
                    raise
                time.sleep(2 * (attempt + 1))
        f.write_text(json.dumps(data), encoding="utf-8")
        self.n += 1
        time.sleep(0.15)
        return data

    def work(self, ref: str) -> dict:
        return self.get(f"{API}/{urllib.parse.quote(ref, safe=':/')}?select=id,doi,title,publication_year,referenced_works")

    def search_title(self, title: str) -> dict | None:
        d = self.get(f"{API}?" + urllib.parse.urlencode({"search": title, "per-page": 3, "select": "id,doi,title,publication_year,referenced_works"}))
        for w in d.get("results", []):
            a, b = set(norm(title).split()), set(norm(w.get("title")).split())
            if a and len(a & b) / len(a | b) >= 0.8:
                return w
        return None

    def citing(self, wid: str, cap: int) -> list[dict]:
        # page= paging works without a key (cursor= paging does not)
        out, page = [], 1
        while len(out) < cap:
            q = urllib.parse.urlencode({"filter": f"cites:{wid}", "per-page": 100, "page": page, "select": SEL})
            d = self.get(f"{API}?{q}")
            out += d.get("results", [])
            if len(d.get("results", [])) < 100:
                break
            page += 1
        return out[:cap]

    def batch(self, ids: list[str]) -> list[dict]:
        out = []
        for i in range(0, len(ids), 50):
            part = "|".join(ids[i:i + 50])
            d = self.get(f"{API}?" + urllib.parse.urlencode({"filter": f"openalex:{part}", "per-page": 50, "select": SEL}))
            out += d.get("results", [])
        return out


def short(u: str) -> str:
    return (u or "").rsplit("/", 1)[-1]


def main(args: list[str]) -> int:
    min_seeds, cap = 2, 400
    if "--min-seeds" in args:
        i = args.index("--min-seeds")
        min_seeds = int(args[i + 1])
        del args[i:i + 2]
    if "--cap" in args:
        i = args.index("--cap")
        cap = int(args[i + 1])
        del args[i:i + 2]
    res, sel, out = args[:3]
    outd = Path(out)
    outd.mkdir(parents=True, exist_ok=True)
    cl = Client(outd / "cache")
    data = json.loads(Path(res).read_text(encoding="utf-8"))
    corpus = data["items"] if "items" in data else data["results"]
    c_w = {short(x["id"]) for x in corpus if short(x["id"]).startswith("W")}
    c_doi = {(x.get("doi") or "").lower().replace("https://doi.org/", "") for x in corpus if x.get("doi")}
    c_title = {norm(x["title"]) for x in corpus}

    wanted = [ln.split(" #")[0].strip() for ln in open(sel, encoding="utf-8") if ln.strip() and not ln.startswith("#")]
    seeds, log = {}, []
    for w in wanted:
        hits = [x for x in corpus if w.lower() in x["title"].lower()]
        if len(hits) != 1:
            log.append(f"SEED PROBLEM {w!r}: {len(hits)} matches in results")
            continue
        it = hits[0]
        ref = None
        if short(it["id"]).startswith("W"):
            ref = short(it["id"])
        elif it.get("doi"):
            ref = "https://doi.org/" + it["doi"].lower().replace("https://doi.org/", "")
        try:
            wk = cl.work(ref) if ref else cl.search_title(it["title"])
        except Exception:  # noqa: BLE001
            wk = cl.search_title(it["title"])
        if not wk or not wk.get("id"):
            log.append(f"SEED NOT RESOLVED {it['title'][:60]!r}")
            continue
        seeds[short(wk["id"])] = (it["title"], wk.get("referenced_works") or [])
    log.append(f"{len(seeds)} of {len(wanted)} seeds resolved in OpenAlex")

    back, fwd, meta = defaultdict(set), defaultdict(set), {}
    for sid, (title, refs) in seeds.items():
        for r in refs:
            back[short(r)].add(sid)
        for c in cl.citing(sid, cap):
            cid = short(c["id"])
            fwd[cid].add(sid)
            meta[cid] = c
    log.append(f"backward: {len(back)} distinct cited works; forward: {len(fwd)} distinct citing works")

    need = [k for k, v in back.items() if len(v) >= min_seeds and k not in meta]
    for w in cl.batch(need):
        meta[short(w["id"])] = w

    rows = []
    for cid in set(back) | set(fwd):
        b, f = back.get(cid, set()), fwd.get(cid, set())
        if cid in seeds or len(b | f) < min_seeds or cid not in meta:
            continue
        m = meta[cid]
        text = (m.get("title") or "") + " " + abstract(m.get("abstract_inverted_index"))
        doi = (m.get("doi") or "").lower().replace("https://doi.org/", "")
        rows.append({
            "id": cid, "title": m.get("title") or "", "year": m.get("publication_year") or "", "doi": doi,
            "n_seeds": len(b | f), "cites_seeds": len(f), "cited_by_seeds": len(b),
            "cited_by_count": m.get("cited_by_count") or 0,
            "in_corpus": int(cid in c_w or (doi and doi in c_doi) or norm(m.get("title")) in c_title),
            "in_window": int(bool(m.get("publication_year")) and m["publication_year"] >= 2019),
            "on_topic": int(bool(DRIVE.search(text)) and bool(TASK.search(text))),
            "on_topic_tight": int(bool(TIGHT_A.search(text)) and bool(TIGHT_B.search(text))),
            "has_abstract": int(bool(m.get("abstract_inverted_index"))),
        })
    rows.sort(key=lambda r: (-r["n_seeds"], -r["cited_by_count"]))
    cols = list(rows[0]) if rows else ["id"]
    with open(outd / "chain_candidates.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, cols)
        w.writeheader()
        w.writerows(rows)

    new = [r for r in rows if not r["in_corpus"] and r["in_window"] and r["on_topic"]]
    log += [f"candidates linked to >= {min_seeds} seeds: {len(rows)}",
            f"  already in corpus: {sum(r['in_corpus'] for r in rows)}",
            f"  not in corpus, 2019 or later, on topic by keyword rule: {len(new)}",
            f"  of those, passing the stricter rule too: {sum(r['on_topic_tight'] for r in new)}",
            f"API requests made (not cached): {cl.n}"]
    (outd / "chain_summary.txt").write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]) if len(sys.argv) >= 4 else print(__doc__) or 2)
