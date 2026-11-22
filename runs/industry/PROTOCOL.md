# Industry scan: autonomous-driving scenario generation, simulation and evaluation

Written 2026-11-22 BEFORE searching. Separate from the 34-paper academic review (runs/tableB); not merged into its table.

## Question
What do companies publicly say they use for (a) generating and controlling driving scenarios, (b) simulation and world models for training and testing, (c) safety evaluation, and how is that changing (2024 onward)?
Assumption: scoped to the review's topic plus the trends it sits in (generative world models, end-to-end driving, simulation at scale). Not a survey of all AV technology.

## Sources allowed (grey literature, labelled)
- primary: company research blogs, technical reports, safety reports, product pages, official talks
- arXiv or conference papers whose authors are at a company (author affiliation read from the paper itself)
- secondary (news, analysts): only to find a primary source, never cited as evidence

## Evidence grades
- A: company primary source states it, with a number or a described method
- B: company primary source, qualitative or marketing wording
- C: secondary report; used only to find A or B
Marketing claims are recorded as claims ("the company states"), not as results.

## Companies to cover (not a ranking)
Waymo, Wayve, Tesla, NVIDIA, Waabi, Zoox, Nuro, Aurora, Applied Intuition, Mobileye, Baidu Apollo, Huawei, XPeng, Li Auto, Momenta, Toyota (TRI/Woven), Bosch.

## Probe list (what a fair scan should find; written from memory before searching)
1. Waymo: published work on simulation or traffic agents (e.g. SimAgents challenge, WOMD) and on a foundation/driving model
2. Wayve: generative world model (GAIA series)
3. NVIDIA: world foundation models for driving (Cosmos) and a simulation platform (DRIVE Sim / Omniverse)
4. Tesla: public statements about end-to-end driving and simulation
5. Waabi: closed-loop simulator (Waabi World)
6. Applied Intuition: simulation / scenario tooling
7. Huawei: public description of its ADS and world-model approach
8. Baidu Apollo: simulation or generative approach
9. Mobileye: simulation or safety-model (RSS) material
10. Zoox or Nuro: simulation / safety evaluation material
Recall = probes found with an A or B source. Misses are reported, not hidden.

## Procedure
search (WebSearch, standard) -> record every candidate URL in candidates.csv with decision and reason -> fetch the page, save plain text in pages/ -> extract rows (company, date, claim, verbatim quote, URL, grade) -> script checks each quote occurs in the saved page text -> report. Unfetchable pages are marked and not quoted.
