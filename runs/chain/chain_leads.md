# Citation chaining from the 34 table papers

Run 2026-11-22 with `tools/chain.py` (OpenAlex). Seeds: the 34 papers of `runs/tableB/selection.txt`, all 34 resolved. Backward = works the seeds cite (649 distinct), forward = works that cite the seeds (1,191 distinct). A candidate is kept only if it links to at least 2 different seeds. Full list: `chain_candidates.csv`; summary numbers: `chain_summary.txt`.

## Result

| Candidates linked to at least | on topic*, 2019 or later | already in the 371-paper corpus | not in corpus |
|---|---|---|---|
| 3 seeds | 191 | 56 (29 %) | 135 |
| 5 seeds | 99 | 33 (33 %) | 66 |
| 7 seeds | 52 | 22 (42 %) | 30 |

\* "On topic" = passes the keyword rule of `merge_results.py` and a stricter one (names scenario or simulation, and a generative or control word, in title or abstract). It is a keyword rule: it lets through datasets, trajectory predictors and surveys, so "not in corpus" is not the same as "a missed relevant paper".

**What it means.** Only about a third of the strongly linked, on-topic papers were in the corpus the review was built from. The earlier probe recall of 15 of 16 was measured against a short list written from memory, with queries added after seeing which probes were missing, and was already flagged as optimistic; this is a second measure, independent of that list, and it is much lower. The one probe paper that the original search had missed, DriveSceneGen, is among the chaining candidates (linked to 3 seeds), so chaining does recover what the keyword search missed.

Of the 66 papers linked to 5 or more seeds and not in the corpus, 49 are from 2025 or 2026 and 17 are from 2024 or earlier. The 2025-26 ones are partly what a search run earlier would not have had; the 17 older ones are real misses of a 2019-onward search.

## Strongest leads (my reading of titles only; none opened)

Controllable or promptable generation and simulation, 2024 and earlier (should have been found):
SceneDiffuser (11 seeds), SceneControl (6), Promptable Closed-loop Traffic Simulation (5), Editing Driver Character: Socially-Controllable Behavior Generation (5), Reinforcement Learning with Human Feedback for Realistic Traffic Simulation (5), Traffic Scene Generation from Natural Language Description with LLMs (5), BITS (14), Symphony (10), MixSim (10), CMTS (5), Generating Adversarial Driving Scenarios in High-Fidelity Simulators (9).

2025 and 2026, controllable or adversarial generation:
LangTraj, Talk2Traffic, Gen-Drive, SEAL, RADE, CaFe, Optimization-Guided Diffusion for Interactive Scene Generation, Decoupled Diffusion Sparks Adaptive Scene Generation, CaDRE, Controllable Multimodal Motion Behavior Generation, Every Scene All at Once, TrafficGamer, DiffSCTG, CrashDiffuser, VILTA, LASER, Guiding Neuro-Symbolic Scenario Generation with Spatio-Temporal Logic.

Surveys (useful as maps, not as table rows): Generative AI for Testing of Autonomous Driving Systems (15 seeds), Adversarial and Reactive Traffic Entities for Behavior-Realistic Driving Simulation, Diffusion Models for Intelligent Transportation Systems, a survey on driving scenario video generation, a survey on generative AI in ADS test scenario generation.

Not scenario papers that the keyword rule let through: nuScenes, Argoverse 2, DDPM and DDIM, MTR, QCNet, MultiPath++.

## Limits

- Titles and abstracts only. Nothing here has been downloaded or read, so none of these can go into the review or the table yet.
- OpenAlex citation links are incomplete, especially for recent preprints, so the counts are lower bounds.
- Seeds are the 34 chosen papers, so chaining follows their neighbourhood. Work in a different corner (for example sensor-level world models) would be reached only through the industry scan or a new search.
- Forward candidates from 2026 may cite the seeds in passing; 2 or more seed links reduces but does not remove that.
- Next step, if these are to enter the review: add the on-topic ones to the screening log, fetch full text with `resolve_oa.py`, then run the table steps for the chosen ones. Not done here.
