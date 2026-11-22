# Industry scan: scenario generation, simulation and evaluation in autonomous driving

Scan date 2026-11-22. Separate from the 34-paper academic review (`../tableB/review_A.md`); not merged into its table. Protocol: `PROTOCOL.md` (written before searching). Evidence: `rows.json` (35 rows, each with a verbatim quote), saved pages in `pages/`, quotes machine-checked by `tools/check_quotes.py` (35 rows, 0 problems; the checker was tested with an injected wrong quote, number and page and caught all three).

Grades: A = company primary source with a described method or a number; B = company primary source, product or marketing wording; C = secondary, used only to find a primary source. Everything below is what a company says in public. It is not a measured result and has not been independently verified.

## 1. What was and was not covered

Web search (14 queries in two rounds, then 3 more for gaps) found candidate pages; I fetched 19 and read the primary ones. The search tool's own summaries were used to find URLs and were not used as evidence.

| Probe written first | Result |
|---|---|
| 1 Waymo simulation / foundation model | Partly: world-model blog found (A); the traffic-agent work (SimAgents, WOMD papers) was not searched or read |
| 2 Wayve generative world model | Found (A): GAIA-2 abstract page. Only the abstract was read, not the report |
| 3 NVIDIA Cosmos and simulation platform | Found (A): 3 blog posts and the Alpamayo release |
| 4 Tesla end-to-end and simulation | Found (A): the abridged ICCV 2025 talk, posted on X by Tesla's VP of AI |
| 5 Waabi closed-loop simulator | Found, but only a 2022 launch post (B); no recent Waabi source was read |
| 6 Applied Intuition | Found (B): Neural Sim announcement. A second page was fetched and not used for rows |
| 7 Huawei ADS and world model | Found (B): the ADS product page, undated, no technical report |
| 8 Baidu Apollo | Missed at primary level: only a wiki page that aggregates news (C). No Baidu primary page was fetched |
| 9 Mobileye | Found (B) for simulation and failure discovery; its safety model RSS was not read |
| 10 Zoox or Nuro | Missed: two Zoox pages came back empty (JavaScript pages), and the Nuro search returned nothing of Nuro's own |

So 7 of 10 probes are fully met, 1 partly, 2 missed. Unprompted finds: XPeng X-World (B), Mobileye Meteor and Genario (B), NVIDIA Alpamayo (A). Not covered at all: Li Auto, Momenta, Toyota, Bosch, Aurora. The X-World arXiv paper behind the XPeng release was not read, and a few probes had only one page, so a company with one row here may have much more public material.

## 2. What the sources say

**Generative world models are replacing reconstruction-based simulation at several companies.** Waymo says purely reconstructive methods such as 3D Gaussian splats "suffer from visual breakdowns" when the route differs from the logged one [W4]. XPeng says the same of them, that they struggle beyond the reconstructed range [X2]. Tesla describes a neural simulator that predicts the next sensor state from the current state and the next action [T1]. Applied Intuition is the counterexample in this set: its Neural Sim turns drive logs into neural reconstructions [A1, A2], so reconstruction is still a product, and that page is from January 2025.

**The base is a large pretrained video or world model, post-trained on driving data.** Waymo builds on Genie 3 [W1], XPeng on the video model WAN 2.2 [X1], NVIDIA publishes Cosmos models post-trained on 20,000 hours of driving [N2]. NVIDIA's stated result is that fog and rain performance improved, with no number given.

**Control comes through a few interfaces.** Waymo names three: driving action, scene layout, language [W3, W2]. Wayve and XPeng condition on structured inputs, namely ego actions, agent states, road elements [Y2, X5]. NVIDIA's Cosmos Transfer varies weather, lighting and terrain of an existing scenario [N3], and Mobileye's Genario varies a found failure across conditions [M2]. Compared with the academic review, language control and trained-in conditioning appear here. Inference-time guidance and reward tilting do not appear on any page I read, which says nothing about whether the companies use them internally.

**The simulator is used in a closed loop with the driving policy.** Tesla connects its simulator to the policy to evaluate it [T2]; XPeng makes its generator streaming and autoregressive for closed loop and online reinforcement learning [X3]; Huawei lists multi-agent game theory and online reinforcement learning on its cloud side [H2].

**The demand comes from end-to-end driving.** NVIDIA says stacks are moving from many models to one end-to-end model, which raises the need for sensor data [N1]. Tesla says end-to-end is not the consensus approach [T4]. NVIDIA positions its reasoning vision-language-action models as teachers to distil from, not as the in-car model [N5].

**Failure discovery is treated as part of generation.** Mobileye finds recurring failures with a multi-agent analyst, then generates variations [M1, M2], and says the aim is to extend real data, not replace it [M3] because more data alone is "necessary, but not sufficient" [M4]. Tesla says it can create adversarial scenarios, with no method or numbers [T3].

**Scale figures are claims and not comparable.** XPeng: scenarios from 30,000 to more than 500,000 in a year [X4]. Tesla: fleet data of 500 years of driving per day [T5]. NVIDIA: 40,000 generated clips released openly [N4].

**Openness differs.** NVIDIA releases models, a simulator and datasets openly [N4, N5, N6]. Waymo, Tesla and XPeng describe closed systems.

## 3. Differences from the academic review

- The industry pages are about **sensor-level** world models (camera and lidar or multi-camera video). The academic review covers scenario and traffic generation. I did not check how many of the 34 papers generate sensor data, so I cannot say how large the gap is.
- No page I read reports a controllability measurement like the dial numbers in the academic review (collision rate against a weight). Waymo shows videos, not numbers [W3]; XPeng lists three strengths without figures [X1, X5]. The X-World paper, which I did not read, may contain them.
- Waabi's "generative AI" statement is from 2022 [B1, B2], so it should not be read as the current state of that system.

## 4. Limits

- Public marketing, blog and talk material only. No source here was peer reviewed, and the numbers are company figures.
- Tesla's source is an X post of an abridged talk, not the video.
- Huawei's page has no date and no method detail; its own disclaimer says the passenger-car system is a driver-assistance feature [H3].
- The Baidu row [D1] is secondary and should not be cited as Baidu's statement.
- Selection is mine and the search is US-oriented, so Chinese-language primary sources are likely under-covered.
- Rows carry a verbatim quote, but whether the claim is a fair reading of that quote was checked only by me, once.
