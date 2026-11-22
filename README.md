# Literature-review baseline (no key, stdlib only)

**Start with [PIPELINE.md](PIPELINE.md)**: the hybrid workflow (literature-review skill's method plus this folder's tools). This README is the run log and test notes.

Source: https://github.com/brycewang-stanford/lit-review-agent-tools (recipes 03 and 06).
Scripts in `vendor/` are unmodified copies, downloaded 2026-11-22. Read before running: they only call public scholarly APIs (OpenAlex, Crossref, Semantic Scholar, PubMed, Europe PMC, arXiv, Unpaywall).
`vendor/scripts/litrun.py` is a pip/venv installer manager; not used.

## Run (Windows, from this folder)

`-I` ignores env vars, so UTF-8 must be set with `-X utf8`.

```
python -I -X utf8 vendor/scripts/fetch_papers.py --query "<keywords>" --sources openalex,crossref,semanticscholar,arxiv --max 15 --dedup-titles --outdir runs/<name>
python -I -X utf8 vendor/scripts/resolve_oa.py --from-json runs/<name>/results.json --outdir runs/<name>
python -I -X utf8 vendor/verify/verify_citations.py <citations.txt>
```

Optional free keys (read from env, only raise rate limits): `S2_API_KEY`, `UNPAYWALL_EMAIL`, `CORE_API_KEY`, `OPENALEX_MAILTO`.

## Smoke-test findings (2026-11-22)

Search, query "controllable traffic scenario generation reward tilting autonomous driving":
- 45 raw, 45 unique, 0 found by more than one source (same as the author's finding: sources barely overlap).
- Semantic Scholar: HTTP 429 without key, so effectively unavailable. Get `S2_API_KEY`.
- Long natural-language query gave noisy hits (tilt cameras, mining, comms). Only 1 known key paper (CtRL-Sim, via OpenAlex); Scenario Diffusion, DragTraffic, Scenario Dreamer also relevant. Use short keyword queries and run several.
- Crossref and arXiv sources returned mostly keyword-matched noise for this query; OpenAlex was the best of the three.

Citation verifier, 5-item test (`runs/cite-test.txt`):
- Real Crossref DOI: CONFIRMED. Retracted Lancet paper: RETRACTED. Invented CtRL-Sim++ title: WEAK MATCH (29%), correctly not confirmed.
- **Gap for ML/AD work:** arXiv DOIs (10.48550/arXiv.*) are DataCite, not Crossref, so a real arXiv paper comes back as WEAK MATCH, indistinguishable from an invented one. Title-only "Attention Is All You Need" returns a different paper (correctly flagged TITLE MATCH, needs a human).
- Fixed in `tools/verify_citations_arxiv.py` (below). vendor/ is kept pristine so results stay comparable.

## arXiv-aware verifier (`tools/verify_citations_arxiv.py`)

Wraps the vendor script (loads it by path, monkeypatches `by_doi` / `by_title`, no copy). Use this one for ML/AD citations:

```
python -I -X utf8 tools/verify_citations_arxiv.py <citations.txt>
```

- arXiv id in any form (`10.48550/arXiv.X`, `arXiv:X`, `arxiv.org/abs/X`, with `vN`) is resolved via the arXiv API and counts like a DOI: CONFIRMED.
- Title lookup also searches arXiv; exact ordered title match beats bag-of-words overlap, so "Attention Is All You Need" now resolves to Vaswani 2017 (still TITLE MATCH, never CONFIRMED).
- Test `runs/cite-test-arxiv.txt` (10 items): 3 arXiv ids CONFIRMED, 2 arXiv titles TITLE MATCH on the right paper, Crossref DOI CONFIRMED, retracted paper RETRACTED, invented title and nonexistent arXiv id both WEAK MATCH. All as intended.
- Limits: a line with both an id and a title only checks the id, so a real id with a wrong title is CONFIRMED. WEAK MATCH and NOT FOUND for a title do not make the exit code non-zero (only not-found DOIs and retractions do), so do not use the exit code as a hallucination gate. arXiv API is throttled to 1 request per 3 s, so about 4 s per citation.

## Full-text retrieval (`resolve_oa.py`, run 2026-11-22)

Input: the 45 smoke-search records. Command: `python -I -X utf8 vendor/scripts/resolve_oa.py --from-json runs/smoke-search/results.json --outdir runs/smoke-fulltext`. 2.5 min, 232 MB, no key.
- 29 of 45 open (28 PDF, 1 Europe PMC XML to txt): 14 via arXiv, 13 via OpenAlex, 1 via search-hit. 13 closed, 1 not in Crossref, 2 errored (one OpenAlex HTTP 403, one arXiv 404).
- All 28 PDFs start with `%PDF-` (no HTML block pages ingested).
- Key papers recovered: CtRL-Sim, Scenario Dreamer, Scenario Diffusion, DragTraffic. Closed: mostly 2025-26 Elsevier/IEEE (TrafficDiff, LLM-Attacker, etc.), so recent journal papers need arXiv versions or institutional access.
- Unpaywall step skipped (needs an email via `--email` / `UNPAYWALL_EMAIL`; not supplied). CORE skipped (no key).
- File names are inconsistent: DOI-based, arXiv-id-based, and one generic `paper.pdf`. Build a manifest from `oa_report.json` before indexing (see paper-qa notes).
- Most of the 29 are search noise, not relevant to the topic; retrieval is fine, query quality is the bottleneck.

## Manifest for paper-qa (`tools/make_manifest.py`)

```
python -I -X utf8 tools/make_manifest.py runs/smoke-fulltext
```
Writes `runs/smoke-fulltext/manifest.csv` (`file_location, doi, title`; set via `agent.index.manifest_file`). 29 rows, all files exist, no duplicate files or DOIs. 12 blank DOIs were filled from the arXiv id in the download URL (`10.48550/arXiv.<id>`); 1 stays blank (`paper.pdf`, no DOI and no arXiv id). Not checked: that each PDF's content matches its DOI (the resolver trusts the source). Column names beyond these three are not verified against paper-qa's `DocDetails`.

## Ported from paper-qa (no install, no key)

Code is in `tools/pqa/` (Apache-2.0 attribution in `tools/pqa/NOTICE.md`). `pqa_port.py` is stdlib-only; `rcs.py` also uses PyMuPDF, already installed.

Flow: **retrieve -> Claude summarizes and scores each chunk -> answer with citation keys**.

```
python -I -X utf8 tools/pqa/rcs.py prepare runs/smoke-fulltext "<question>" --out runs/rcs1   # writes packets.jsonl
# answer each packet's system+user prompt (yourself or a Claude Code subagent); save {"key","reply"} lines to runs/rcs1/replies.jsonl
python -I -X utf8 tools/pqa/rcs.py collect runs/rcs1                                           # writes qa_prompt.md
```

What was ported: prompts (summary JSON, QA, citation-key rules), tolerant JSON/score parsing, `strip_citations`, page-aware chunking (5000 chars, 250 overlap), MMR, paper-qa defaults (k=10, 5 sources, score cutoff 1). Replaced: the embedding model, with a small TF-IDF index (not from paper-qa), so retrieval is lexical, not semantic.

Tested 2026-11-22:
- `prepare` on the 29-paper corpus: 478 chunks, 10 packets in 4 s; all packets from relevant papers (Scenario Dreamer, DragTraffic, CtRL-Sim, Scenario Diffusion, Guided Latent Spaces), 7 of 29 papers covered.
- `collect` on 8 synthetic replies (parser test only, not model output, since deleted): fenced JSON, `"7/10"`, trailing comma, `Score: 6` text, `Not applicable`, alternate key `score` all parsed; garbled reply and unknown key reported, not crashed. Quirk inherited from paper-qa: `strip_citations` leaves a stray `)` on nested parentheses.
- Not tested: real summaries by Claude, and answer quality. Lexical retrieval may miss papers that use different wording.

Verifier improvement (inspired by paper-qa's title+author queries): `tools/verify_citations_arxiv.py` now also checks that the line's own text agrees with the title the id resolves to. Test `runs/cite-test-mismatch.txt`: real arXiv id with wrong title and real Nature DOI with wrong title both flagged `! ID/TITLE MISMATCH`, not CONFIRMED; correct lines (including ones with author/venue noise) still CONFIRMED; earlier regression set unchanged. Limit: lines with fewer than 4 words besides the id are not checked, and authors are not compared.

### Full run (2026-11-22): `runs/rcs1`

Question: "How is controllability achieved in driving scenario generation models?" Corpus: the 29 papers in `runs/smoke-fulltext`.
`prepare` (4 s) -> 10 packets -> each summarized and scored by Claude in the same session (`replies.jsonl`) -> `collect` -> answer (`answer.md`) -> sources checked with `verify_citations_arxiv.py` (5 of 5 CONFIRMED, 0 mismatch).

- The score step did its job: ControlNeXt (image generation) got 2 and a textbook PPO chunk got 0 and were dropped, though lexical retrieval had ranked them in the top 10.
- Answer groups methods into three routes: return/reward tilting (CtRL-Sim), attribute conditioning of diffusion (Scenario Diffusion, DragTraffic), structured latent space (guided VAE). Every claim traces to a kept packet; one claim I wanted (DragTraffic via cross-attention) was left out because it was only in a dropped packet.
- Weaknesses seen:
  - No per-paper diversity: top 5 held DragTraffic twice, and Scenario Dreamer was dropped on a score tie (its retrieved chunk was an appendix about CtRL-Sim, not its own method). paper-qa has the same top-k-by-score rule; a cap of 1-2 chunks per paper would help.
  - 3 of the 10 packets came from one paper; only 7 of 29 papers were covered.
  - The summarizer and the answerer were the same session, so there is no independent check; summaries were not re-verified against the PDFs beyond reading the packets.
  - The answer is only as broad as the 29-paper corpus, which came from one noisy query. It misses well-known works (CTG, CTG++, Trajeglish) that were not retrieved.

## Expanded corpus (`runs/corpus2`, 2026-11-22)

- 13 short keyword queries (OpenAlex + arXiv, from 2019), merged with `tools/merge_results.py`: 636 raw, 536 unique, 371 after a loose keyword filter (a tighter rule lost 2 of 16 known papers, so it was not used).
- Recall probe (`known_papers.txt`, 16 titles recalled from memory, titles of the 5 initial misses confirmed to exist in OpenAlex): 3 of 16 from the first search, 15 of 16 after the queries. Biased upward: the last 5 queries were added after seeing which probes were missing. DriveSceneGen is still missing.
- Full texts (`resolve_oa.py`, 369 targets, ~20 min, 1.9 GB, no key): 288 open (282 PDF, 6 XML to txt), 70 closed, 6 DOIs unknown to Crossref, 5 errors. All PDFs start with `%PDF-`. `manifest.csv` has 288 rows (76 DOIs derived from arXiv ids, 4 blank).

## Comparison table B (`runs/tableB`)

Per-paper evidence packets (`tools/table_packets.py`: first two pages plus the best 2 passages per field query inside that paper), 34 papers chosen from abstracts across control mechanisms (`selection.txt`), rows filled by six parallel Claude sub-agents under a strict schema (page per value, "not stated in packet" when unsupported), checked by `tools/assemble_table.py` (schema, pages, and every number must occur in the packet).

Result (2026-11-22): 34 rows, `table.md`; automated check 0 issues (checker verified to catch injected fake numbers, missing pages, bad labels; its number test is weak for short numbers). 4 rows hand-checked against packets: correct. Independent random audit by a separate sub-agent, 24 cells (mechanism and evidence for 12 papers): 22 supported, 2 partial, 0 unsupported, 0 page mismatches; both partial cells fixed. Other fields (data, metrics, limitations) not audited. Families: inference-time guidance 9, language/LLM 5, trained-in conditioning 5, reward/return 3, RL fine-tuning 2, latent 2, other 4, no control 4 (realism-only simulators the search returned).

## Review A (`runs/tableB/review_A.md`)

Written only from table B (about 2,200 words, 34 references, every reference cited). Sections: taxonomy by where the control signal enters, what the rows show per family, cross-cutting observations, gaps, validity. No cross-paper ranking, since metrics and data differ. Reference list has titles, years and DOIs but no authors (author order in the search metadata is inconsistent). No person has read the PDFs.

## Ideas from paper-qa not ported

- Agent loop with LLM-written keyword queries (do this in Claude Code, not in code).
- Index persistence and incremental add; metadata clients and journal-quality data; multimodal enrichment (docling/nemotron readers).

## Ideas to borrow from paper-qa (original list) (read README only, not installed)

- Manifest CSV (`file_location, doi, title`) so metadata is not LLM-guessed. Generate it from `oa_report.json`.
- Contextual summarization: retrieve top-k chunks, LLM scores and summarizes each against the question, re-rank, answer from the best few (k > max_sources). Can be done with Claude Code subagents, no extra key.
- Metadata lookup by title plus authors (and optional `fields`) to disambiguate; closes the verifier's "real id, wrong title" gap.
- Agent loop with tools (search, gather evidence, answer) in any order, with LLM-written keyword queries; fixes the noisy long-query search.
- Index hashed on settings, incremental add, answers saved and searchable.
- Its own FAQ: the open-source version expects you to bring the PDFs, which is what the steps above produce.

## Not done yet

- paper-qa not installed (needs an LLM key, Python 3.11+; compatibility with Python 3.14 not checked).
- Relevance filtering of the retrieved corpus is a keyword rule only (`tools/merge_results.py`); no ranking beyond it.
- Later work (selection reasons, citation chaining, claim check, industry scan, slides, PDF, API mode via `tools/llm_run.py`) is described in [PIPELINE.md](PIPELINE.md), not in this log. `llm_run.py` was tested against a mock server only.
- `runs/*/fulltext/` (downloaded PDFs, about 2 GB), the evidence packets, the saved web pages of the industry scan, the OpenAlex cache and the exported slide and page images are not in version control; regenerate them with the commands in PIPELINE.md.
