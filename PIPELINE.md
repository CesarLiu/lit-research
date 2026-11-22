# Hybrid literature-review pipeline

Frame from the `literature-review` skill (scope, written criteria, documented search, screening log, thematic synthesis, verified citations). Data layer from this folder (scripted search, full text, per-paper evidence, grounded checks). Run from `lit-review-baseline/`. Every command below was run on the controllable-scenario-generation data (`runs/corpus2`, `runs/tableB`).

Windows: use `python -I -X utf8` (`-I` ignores `PYTHONUTF8`).

## Division of labour

| Who | Does |
|---|---|
| You | Question, inclusion criteria, **probe list of core papers written before searching**, final reading of a sample |
| Claude (in session) | Query wording, picking papers for the table with a recorded reason, per-paper extraction (sub-agents), synthesis |
| Scripts | Search, merge, screening log, full text, evidence packets, table checks, reference formatting, citation check |

## Phases

| # | Phase (skill name) | Do | Command | Output | Check before moving on |
|---|---|---|---|---|---|
| 0 | Planning and scope | Write the question, date range, inclusion and exclusion rules, and the probe list (10-15 core papers, titles) in `runs/<name>/PROTOCOL.md` and `known_papers.txt` | by hand | protocol, probes | Probes written **before** the first search |
| 1 | Search | 8-13 short keyword queries, then targeted ones for gaps | `python -I -X utf8 vendor/scripts/fetch_papers.py --query "<kw>" --sources openalex,arxiv --max 25 --from-year 2019 --dedup-titles --outdir runs/<name>/search/q1` | `q*/results.json` (query, sources, counts, errors) | Semantic Scholar needs `S2_API_KEY`, else HTTP 429 |
| 2 | Aggregate and screen | Deduplicate, keyword rule, record every decision with its reason | `python -I -X utf8 tools/merge_results.py runs/<name>/results.json runs/<name>/search/q*/results.json --filter --known runs/<name>/known_papers.txt --log runs/<name>/screening_log.csv` | merged list, `screening_log.csv` | Probe recall printed; no probe lost by the filter |
| 3 | Full text | Open-access PDFs, no paywall bypass | `python -I -X utf8 vendor/scripts/resolve_oa.py --from-json runs/<name>/results.json --outdir runs/<name>/fulltext` then `python -I -X utf8 tools/make_manifest.py runs/<name>/fulltext` | PDFs, `oa_report.json`, `manifest.csv` | Counts of open, closed, errors |
| 4 | Flow counts | PRISMA-style counts from the artefacts | `python -I -X utf8 tools/prisma.py runs/<name>/screening_log.csv runs/<name>/fulltext runs/<table> runs/<name>/PRISMA.md` | `PRISMA.md` | Numbers add up at every step |
| 4b | Citation chaining | From seed papers (the probes and the strongest on-topic hits; here the 34 table papers), list works they cite and works that cite them, keep those linked to 2 or more seeds. Leads go back into phase 2 and 3 | `python -I -X utf8 tools/chain.py runs/<name>/results.json <seeds.txt> runs/<name>/chain` | `chain_candidates.csv`, `chain_summary.txt` | Share of strongly linked on-topic papers already in the corpus (here 33 % at 5 or more seeds) = a recall estimate independent of the probe list; leads are title-level until read |
| 5 | Select for synthesis | Claude ranks abstracts (`pqa_port.TfidfIndex`), proposes papers; you may edit. One line per paper, ` # reason` after the title substring | write `runs/<table>/selection.txt` | selection with reasons | Every paper has a reason; every one has full text |
| 6 | Data extraction | Evidence packet per paper, split ids into groups, then one sub-agent per group fills the rows with the saved prompt `runs/<table>/prompts/extract_row.md` | `python -I -X utf8 tools/table_packets.py runs/<name>/fulltext runs/<table>/selection.txt runs/<table>/packets`, then `python -I -X utf8 tools/prep_agents.py groups runs/<table> 6`, then per group `python -I -X utf8 tools/prep_agents.py render extract_row runs/<table> <abs path of gK.txt>` and give the output to the sub-agent | packets, `gK.txt`, `rows/*.json` | See phase 7 |
| 7 | Quality control | Schema, pages, numbers in packet; independent audit of a random sample | `python -I -X utf8 tools/assemble_table.py runs/<table>`, then `python -I -X utf8 tools/prep_agents.py audit runs/<table> 12 <seed>` and render `audit_cells` to a separate sub-agent | `table.md`, `check.txt`, `audit_cells.json`, `audit_result.json` | `check.txt` clean; audit has 0 unsupported, fix partials; hand-check some rows yourself |
| 8 | Synthesis | Thematic review **from the table only**, citing `[n]` | Claude writes `review_A.md` | review | Every claim traces to a row; no cross-paper ranking when metrics differ |
| 8b | Claim check | Every sentence of the review is checked against the cited table rows by a checker that did not write it, preferably another model | `python -I -X utf8 tools/split_claims.py runs/<table>/review_A.md runs/<table>/refs.json runs/<table>/rows runs/<table>/claims 4`, run `prompts/claim_check.md` on each `claims_K.json`, then `python -I -X utf8 tools/summarize_claims.py runs/<table>/claims runs/<table>/claim_check.md` | `claims/`, `claim_check.md` | No UNSUPPORTED; every PARTIAL either fixed in the review or accepted with a reason. First run on the 34-paper review: 49 claims, 26 supported, 19 partial, 1 unsupported, 3 not checkable (`claim_check.md`). After revising the text: 52 claims, 39 / 10 / 0 / 3 (`claim_check_v2.md`, `claims_v2/`); after a second revision the 14 changed sentences were re-checked alone, 12 supported and 2 partial (`claims_v3/`), then reworded without a further check. Each pass found new issues in text it had already seen, so stop on a rule (no UNSUPPORTED, remaining PARTIALs written down), not on "clean" |
| 9 | Citation verification | Reference list with authors, then DOI, retraction, id-vs-title check | `python -I -X utf8 tools/format_refs.py runs/<name>/results.json runs/<table> runs/<table>/references.md`, then `python -I -X utf8 tools/verify_citations_arxiv.py <file>` | `references.md`, verifier log | See notes below |

## Optional: slides from the review

`python -I -X utf8 tools/make_deck.py runs/<table>/deck.pptx` builds an editable deck with speaker notes (12 slides, about 14 min at 105 words/min after the revision that followed the claim check; the earlier deck is kept as `runs/tableB/deck_before_revision.pptx`). When `review_A.md` changes, re-read the slide text in `make_deck.py` against it: the deck is not regenerated from the review. The slide text is written by hand in `make_deck.py` from `review_A.md` and `table.md` (Claude does the extraction; the script only renders). `python -I -X utf8 tools/check_deck.py runs/<table>/deck.pptx runs/<table>/review_A.md runs/<table>/table.md runs/<name>/PRISMA.md` checks that no slide has an em dash, every number on a slide occurs in the sources and is spoken in the notes, and text boxes are not obviously too long. PowerPoint on this machine can export the slides to PNG for a visual check (COM, `SaveAs(..., 18)`). Colour is one per control family, matching the chart on slide 3.

## Provenance manifest (`tools/manifest.py`)

Each run folder (`runs/corpus2`, `runs/tableB`, `runs/chain`, `runs/industry`) has a `MANIFEST.jsonl`: one line per step with the command, SHA-256 of the inputs and outputs (a folder is hashed from its files; big folders such as downloaded PDFs are recorded as file count and bytes only), git commit and whether `tools/` had uncommitted changes, Python version, the model, and whether the step is deterministic.

- Run a step and record it in one go: `python -I -X utf8 tools/manifest.py run runs/<table> --step assemble_table --inputs runs/<table>/rows runs/<table>/packets --outputs runs/<table>/table.md runs/<table>/check.txt --deterministic -- python -I -X utf8 tools/assemble_table.py runs/<table>`. Nothing is recorded if the command fails.
- A step done by sub-agents or by hand: `manifest.py record ... --cmd "<what was done>" --model "<model>"`. If an `llm_log.jsonl` sits next to the outputs, its models and request count are added (this is what `llm_run.py` writes).
- `manifest.py verify runs/<table>` reports OK, CHANGED or MISSING for each output (checked against the latest record that lists it) and "inputs changed since this step ran" where an output may be stale; `manifest.py show` lists the steps.
- **What it proves and what it does not.** It shows which files a step used and that files are unchanged since recorded. It does not re-run the command, so it does not prove the command reproduces the output. Only `deterministic` steps (search merging, PRISMA counts, table assembly, reference formatting) are expected to give the same bytes; model steps, live web or API fetches, and pptx or pdf files are not.
- **Backfilled records.** The existing runs were recorded on 2026-11-22 after the fact (`"backfilled": true`): hashes are of the files as they were that day, commands are the ones in this file, and the model for sub-agent steps is recorded as "session default (not recorded)". Notes on each record say where the text has since changed, for example the review was revised after the claim checks.
- Hashes are of the bytes on this machine. A checkout on another machine may convert line endings and then show CHANGED for text files.

## Evidence completion round (2026-11-22): from chaining leads to a 77-paper table

Chaining (phase 4b) showed the 34-paper table was built on an incomplete search, so its leads were taken through the normal steps. Review `review_A.md` still describes the 34 papers; the larger table has not been written up yet.

1. **Screen** every lead linked to at least 3 seeds (`python -I -X utf8 tools/chain_leads.py`, 135 leads; abstracts for 120). One decision and reason per lead in `runs/chain/chain_screening.csv`: 62 include (60 steerable generation or simulation methods, 2 realism-focused contrast cases), 20 deferred (on topic but only 3 seed links), 53 exclude (surveys, benchmarks, platforms, datasets, planners, trajectory prediction, realism-only simulators, sensor-level simulators). Decisions are my reading of titles and the first part of abstracts (15 leads had no abstract: title only); nobody else has checked them.
2. **Records and full text**: `tools/leads_to_records.py` (OpenAlex metadata, no key) then `vendor/scripts/resolve_oa.py` into `runs/chain2/fulltext`, then `tools/arxiv_fallback.py` (an exact-title arXiv copy for papers that stayed closed). 62 included: 40 open through resolve_oa, 3 more through arXiv, 19 closed (mostly 2025-26 IEEE and Elsevier papers).
3. **Packets, rows, checks** exactly as phases 5 to 7, in `runs/tableC` (34 old rows copied from `runs/tableB`, 43 new): 6 sub-agents on the saved `extract_row` prompt, `assemble_table.py` 0 issues, independent audit by an opus sub-agent of 24 cells from 12 randomly chosen new papers: 22 supported, 2 partial, 0 unsupported, no page mismatches (the two were corrected).
4. **Coverage of the strongly linked on-topic leads** (new, 2019 or later, strict keyword rule), before and after: of the 99 linked to at least 5 seeds, 33 were in the original corpus; now 29 more are in the table, 14 were included but have no open full text, 23 were screened out with a reason, none is unaddressed. Papers with full text in the table: 62 of 99, or 76 of 99 counting the closed ones. The 20 deferred leads (3 seed links) are not counted.

What this does not fix: the screening is mine and unreviewed; 7 of the 43 new rows are flagged in their own notes as not really controllable generation (BITS, Symphony, DriveSceneGen, SymDrive, VILTA, CARS, Path Diffuser); closed papers are absent by construction; the new rows have the same partial-packet limits as the first 34 (some flattened tables); a second chaining round from the 77 papers would find more.

## Atomic-claim ledger (`tools/ledger.py`): from a paper's number to a reproduction record

The claim check links review sentences to table rows. The ledger goes one step further back: each number a paper reports, as one row, with the record of whether anyone reproduced it. It is the contract between this pipeline and whatever runs the code (Claude Code, OpenResearch, openscience, by hand); this pipeline does not run experiments.

1. **Extract** (model step, prompt `prompts/atomic_claims.md`): one JSON per paper in `runs/<table>/atomic/<id>.json`, at most 6 claims, each with one number, its condition, a baseline, a **verbatim quote** and a page. Session: `tools/prep_agents.py render atomic_claims runs/<table> <group file>` to a sub-agent. API: `tools/llm_run.py atomic_claims runs/<table>` (retries on failed checks).
2. **Check**: `python -I -X utf8 tools/ledger.py check-extract runs/<table>`. Hard problems: quote not in the packet, number not in the packet, no number, missing field. Soft: number not in the quote, more than one number per claim, quote over 30 words.
3. **Build**: `ledger.py build runs/<table>` writes `ledger.csv` (refuses to overwrite, because a rebuild would erase registrations; `--force` if you mean it). `code_url` is a code-host link found in the evidence packet, with where it was found. It is a lower bound (the packet is partial), a link on a later page may be another paper's code, and it is not checked to work.
4. **Register before running**: `ledger.py register runs/<table> P05-C1 --tolerance rel:0.05 --budget "GPU-h 8" --approved-by <name>`. This sets the pass criterion, the budget and who approved. A registration cannot be changed afterwards. Then **commit** the ledger.
5. **Run the experiment** elsewhere, then `ledger.py result runs/<table> P05-C1 --status reproduced --observed 60.2 --run-ref <log path>`. It refuses unless the **committed** ledger already holds the same tolerance, budget, approver and registration time, and refuses `reproduced` when the observed number is outside the tolerance (use `partial` or `not_reproduced`).
6. **Check the ledger**: `ledger.py check runs/<table>` (statuses, registration before result, observed after registered, tolerance respected).

What it does not do: it cannot tell whether a person really approved (it records the name you pass), whether the run log is genuine, or whether the code is the paper's. Extraction can miss claims or mis-split a flattened table; spot-check it as you do the rows. Claims with more than one number can only be marked `partial` by hand.

**Pilot (2026-11-22)**, 7 papers chosen because their packets state a code link, plus CtRL-Sim (the one closest to the user's research; its packet states no link): 30 claims from 6 papers in `runs/tableB/ledger.csv`, all `not_attempted`. Only 6 of the 34 papers state a code-host link in their packet, so most of the table cannot be reproduced without code. One paper (CCDiff) gave no claims because its numbers sit in flattened tables.
- The extraction check passes (0 hard problems). 13 of the 30 claims have a quote that is a flattened table fragment, so the row and column of the number rest on the model's reading of line order. An independent opus audit of all 30 claims found 28 supported, 2 partial, 0 unsupported, no page mismatches (`runs/tableB/atomic_audit/`); the two partial claims were corrected by hand (one baseline is unclear in the packet itself). These 13 stay flagged `MAPPING UNVERIFIED` in the ledger, and `register` refuses them until a person checks the packet or paper and passes `--mapping-checked NAME`.
- Nothing has been registered or run. The code links were not opened; one (`github.com/RoboSafe-Lab`) is an organisation page, not a repository.

## Two ways to run the model steps

Four steps need a model and have a fixed prompt in `runs/<table>/prompts/`: `extract_row` (phase 6), `audit_cells` (phase 7), `claim_check` (phase 8b), `atomic_claims` (the ledger below; its API mode was only dry-run, the session mode was the one used). Both ways read the same prompt files and write the same output files, so every later script (`assemble_table.py`, `summarize_claims.py`, the deck and reference tools) works with either.

| | In Claude (session) | API (OpenAI-compatible endpoint, e.g. a local vLLM server) |
|---|---|---|
| Who runs the step | Claude sub-agents, one per group or chunk, which read and write files themselves | `tools/llm_run.py STEP RUN_DIR`, one request per paper, cell or claim; data is put into the message, the reply must be one JSON object |
| Prompt | `python -I -X utf8 tools/prep_agents.py render STEP RUN_DIR <file>` and paste it to the sub-agent | The same template file with the paragraphs about reading and writing files replaced (`to_api()`); all rule paragraphs word for word. `--dry-run` prints it |
| Model | Set per sub-agent (the Agent tool takes a model); the default is the session's model | `--model` / `LLM_MODEL`, `--base-url` / `LLM_BASE_URL` (default `http://localhost:8000/v1`), key from the env var named by `--api-key-env` |
| Checks | `assemble_table.py` and a separate audit afterwards | Same code (`assemble_table.check_row`) on every reply; a bad reply is re-asked with the problems listed (`--retries`, default 2); a row that still fails hard checks is not written |
| Record | Not recorded unless you note it | `llm_log.jsonl` next to the outputs: model, URL, attempts, token usage, problems |

Example for a local vLLM server (`vllm serve <model>`): `LLM_MODEL=<model> python -I -X utf8 tools/llm_run.py extract_row runs/<table> --out-dir runs/<table>_api --workers 8`, then the same for `audit_cells` and `claim_check` with a different `--model` or server.

Safeguards in `llm_run.py`: it never overwrites an existing output unless `--force`; `--out-dir` keeps an API run apart from a Claude run so the two can be compared; an item whose prompt exceeds `--max-prompt-chars` is skipped and reported.

What was tested: plumbing only, against a mock server written for the test (key check, JSON in a code fence, invalid family, a number not in the packet, non-JSON reply and the retries that followed, keep and refuse-to-overwrite rules, output shape accepted by `assemble_table.py` and `summarize_claims.py`). **Not tested: a real vLLM server or any real model**, so the quality of a local model's rows, audits and claim checks is unknown. Sizes to plan for: the longest evidence packet is about 34,000 characters (roughly 10,000 tokens); a claim check that needs the whole table is about 14,000 tokens plus the claim, so serve the model with a context of at least 16,000 tokens, 32,000 to be comfortable. Do not use the same model to extract and to check.

Steps that stay session-only for now: query wording, picking papers (phase 5), the review text itself, slides, the industry scan, and reading chaining leads. They are open-ended and need tools or judgement that one request per item does not cover.

## Optional: industry scan (grey literature, separate from the academic table)

Company blogs, technical reports and talks are not in OpenAlex or arXiv, so they get their own run: `runs/industry/`. Steps: `PROTOCOL.md` with probes written first; WebSearch to find URLs (its summaries are leads, never evidence); list pages in a TSV (`id, company, grade, url`) and `python -I -X utf8 tools/fetch_pages.py URLS.tsv runs/industry/pages` to save plain text (JavaScript-only pages come back nearly empty and are flagged); read the saved pages and write `rows.json` with a verbatim quote per claim and a grade (A primary with method or number, B primary marketing, C secondary); `python -I -X utf8 tools/check_quotes.py runs/industry/rows.json runs/industry/pages` checks every quote occurs in its page, claim numbers occur in the page, and grades are valid. Then `industry_scan.md`. Result on the first run: 35 rows, 7 of 10 probes met, 2 missed (Baidu primary, Zoox/Nuro). Rows are company statements, not results; do not merge them into the academic comparison table.

## Optional: PDF of the review

The installer (winget MSI) is blocked by machine policy here (Error 1934), so pandoc 3.14 is the portable zip from github.com/jgm/pandoc, unpacked to `C:\Users\User\tools\pandoc\x\pandoc-3.14`. xelatex is in `C:\texlive\2025\bin\windows`. From `runs/<table>/`, with both on PATH: `pandoc review_A.md -o review_A.pdf --pdf-engine=xelatex -V geometry:margin=2.2cm -V fontsize=11pt -V colorlinks=true` (6 pages for the 34-paper review; the 3-column taxonomy table breaks across a page with its header repeated). Not run through the skill's `generate_pdf.py`.

## Notes learned from running it

- **Sub-agent prompts.** The exact prompts of the 34-row run were recovered from the session transcript and saved in `runs/tableB/prompts/` (`extract_row.md`, `audit_cells.md`; the six extraction calls differed only in the group file, the two audit calls were identical). `tools/prep_agents.py render` reproduces the first one byte for byte. The model was not pinned: the sub-agents ran on the session's default model, which was not recorded. The 12-paper audit sample of that run came from an unsaved random draw, so a new draw with `prep_agents.py audit` will differ.

- **Verifier input.** For references with a DOI, pass the whole line (this also checks that the text agrees with the title the DOI resolves to). For references **without** a DOI, pass the title alone: with authors and venue in the line, title overlap drops and correct papers show as WEAK MATCH. On the 34-reference list: 31 confirmed by DOI; the 3 DOI-less ones were WEAK MATCH as full lines and TITLE MATCH at 100 % as titles (right title, first author and year; a person still has to accept title matches).
- **Reference metadata is not clean.** Author order is mixed in the search data (surname rule in `format_refs.py`), the venue sometimes shows a preprint server although a published version exists, and some records have no DOI. Check before citing.
- **Screening is only partly reasoned.** Keyword-rule exclusions and duplicates have a logged reason. The choice of table papers has a reason only if you write it in `selection.txt`; the 34 in `runs/tableB` were chosen before this existed, so their reasons were reconstructed afterwards from the table rows (stated in the file header) and describe each paper's role, not the judgement made at the time. The 254 papers with full text that were not chosen have no per-paper reason.
- **Chaining showed the search was incomplete.** Chaining from the 34 table papers (`runs/chain/chain_leads.md`) found 66 on-topic papers linked to 5 or more seeds that are not in the 371-paper corpus, including controllable-simulation papers from 2024 and earlier (e.g. SceneDiffuser, SceneControl, Promptable Closed-loop Traffic Simulation) that the keyword queries missed. They are leads read from titles only; the review and table do not include them. OpenAlex needs no key for `page=` paging, but `cursor=` paging needs a free key (HTTP 401), so `chain.py` uses `page=`.
- **The probe list is only fair if written first.** In the controllable-scenario run, queries were added after seeing which probes were missing, so 15 of 16 is optimistic.

## Taken from the skill, and not

Taken: protocol first, documented queries and counts, screening log and flow counts, thematic synthesis from extracted data, mandatory citation verification, limitations section.
Not integrated (still usable alone): PDF and citation-style output (`generate_pdf.py`, needs pandoc and LaTeX; not checked here), biomedical quality tools (Cochrane, Newcastle-Ottawa), citation-count and venue-tier prioritisation (it would drop most 2025-26 arXiv work), the mandatory AI-generated figures, `gget`/`bioservices` database access.
Citation chaining: skill lists it as a method; here done with OpenAlex links (phase 4b), once, with leads not yet screened or read.

## Run order for a new topic

0 → 1 → 2 → (re-query for gaps, repeat 1-2) → 3 → 4 → 5 → 6 → 7 → 8 → 9. Expect about 20 minutes of full-text download per 370 targets, and tokens for 34 sub-agent rows plus one audit agent.
