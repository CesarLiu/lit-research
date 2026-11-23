# Controllable scenario generation and world models for autonomous driving: evidence from 141 papers and company statements, November 2026

*Built from three evidence sets: a table of 77 papers on scenario and traffic-simulation generation, a table of 64 papers on driving world models, and 41 statements from companies. Bracketed numbers such as [107] are papers in the reference list; bracketed codes such as [W1] are company statements listed in the appendix. Every sentence in sections 1 to 6 was checked by a second model against the table rows or company quotes it cites (see section 8). Nobody has read the full PDFs, and the sections on open problems are my proposals, marked as such.*

## 1. Scope and evidence

The question is how a user or designer steers a generative model of driving, and what that steering reaches. Two layers matter. At the **scenario level** a model generates or simulates the trajectories of road users on a map. At the **sensor level** a world model generates what the vehicle's cameras, lidar or occupancy sensors would see, usually conditioned on an ego action, a layout or text. Company systems combine both.

- **Scenario-level table, 77 papers.** A keyword search of OpenAlex and arXiv (2019 onward) found 371 candidates, of which 288 had open full text; 34 were chosen from abstracts. Citation chaining from those 34 then led to 135 further leads, of which 62 were taken in (43 with open full text). The table has one row per paper under one schema.
- **World-model table, 64 papers.** Ten searches (2023 onward) gave 298 unique records and 230 after a keyword filter; 104 were judged in scope by title and abstract, and 64 were tabled: the 14 probe papers I wrote down before searching, four analyses of control in world models, and the rest by citation count or, for recent work, by emphasis on control. Of the 14 probes, 13 were found by the first nine searches and the last one only after a targeted query added after the miss.
- **Company statements, 41.** Quotes from company blogs, papers and product pages (Waymo, Wayve, NVIDIA, Tesla, XPeng, Huawei, Mobileye, Applied Intuition, Nuro, Waabi), graded A (primary source with a method or number), B (primary, marketing wording) or C (secondary).

What the sources are not. Closed-access papers are absent by construction (19 of the 62 chaining leads and none of the 64 world-model papers had no open copy). 20 scenario-level and 40 world-model papers judged in scope were not tabled. Each row comes from a partial evidence packet (the first two pages plus the best passages), so "not stated" in a row does not mean the paper omits it. Company statements are claims, not results.

## 2. Two layers and one question: where does the control signal enter?

Controllability is not one property. The tables separate **what is specified** from **where it enters the model**.

**Scenario level (77 papers).** Trained-in conditioning is the largest family (18), then inference-time guidance (17), language or LLM-driven methods (13), other methods such as black-box adversarial search (11), models with no steering signal kept for contrast (7), reinforcement-learning fine-tuning (5), latent-space control (3) and reward or return conditioning (3). 32 of the 77 papers are from 2026 and 18 from 2025.

**Sensor level (64 papers).** The families are defined by the signal: ego action or trajectory (19), layout, box, map or BEV conditioning (16), unified multi-condition control (16), text or language (4), inference-time guidance or editing (3), prediction without a control input (2), other (2), camera or viewpoint (1) and scenario, risk or event conditioning (1). 20 of the 64 are from 2024, 23 from 2025 and 17 from 2026.

The two layers share the same injection mechanisms (cross-attention, adaptive normalisation, a ControlNet-style branch, token conditioning, guidance at sampling time) but differ in what the signal means: a risk level, a goal point or a language clause at the scenario level; an ego pose, a box layout or a weather prompt at the sensor level.

## 3. Controllable scenario generation

### 3.1 Inference-time guidance gives a dial, at a price in realism

Seventeen papers are labelled inference-time guidance. In Safe-Sim, raising the time-to-collision cost weight from 0.0 to 1.0 to 2.0 raises the collision rate from 48.2 to 53.6 to 60.7 %, and the realism score worsens from 0.76 to 0.81 (lower is better) [107]. In [98] raising the pursuit weight from 10 to 60 together with the step size from 0.05 to 0.10 lifts the ego-adversary collision rate from 18.9 % to 47.8 %, so the rise cannot be credited to the weight alone. Signal temporal logic rules steer a diffusion model with a rule-violation rate of 0.019 on the speed-limit rule against 0.038 and 0.033 for two optimisation baselines [60]. Risk-level knobs are among the best measured: in [99] the mean crash rate rises from 20.6 % to 50.6 % as the requested risk increases, and in [66] 1,422 of 1,440 requested risk percentiles are realised within 0.05 (98.75 %).

Guidance is not always a gradient. SocialDriveGen uses a gradient-free evolutionary search [119], and OMEGA re-anchors each denoising step by constrained optimisation, raising the valid-scene rate in a goal-conditioned setting from 11.00 % to 80.00 % [91]. SceneDiffuser applies hard constraints after each denoising step; collision constraints raise the collision score from 0.692 to 0.841, while an LLM-written constraint for long-tail agents succeeded in 40 of 100 manually judged samples [115].

### 3.2 Trained-in conditioning is tested most directly, but only for what was trained

DragTraffic conditions agents on type, size and start and target states; with the condition the scenario collision rate at a 9 s rollout is 3.33 % against 13.59 % for a mixed-training baseline, although the row notes that its control evidence is mostly qualitative [32]. Scenario Diffusion keeps the agent-token match rate at 0.97 from 0 to 50 % masking while the number of extra generated agents rises from 0.4 to 12.6 [111]. A multimodal prompt interface (goal points, route sketches, action tags and text) gives a goal-point ADE of 0.3882 m, a 59.12 % gain over no prompt, and 0.2877 m with all prompts [97]; this measures realism against ground truth, not prompt adherence. Courtesy can be set as a scalar and correlates with the input quantile at 0.60 (0.79 on the high-courtesy subset) [49]. A style variable for criticality moves the collision rate of one planner from 4.2 % at -2.0 to 95.3 % at 2.0 [29].

Coverage of a control is limited by training. ECoSim reduces control error by up to 83 % but its evaluation controls are derived from ground-truth trajectories, and it controls a single agent [47].

### 3.3 Language control passes through code, retrieval or text conditioning, and reliability is thinly measured

Thirteen papers are labelled language or LLM-driven, but they work in different ways. ChatScene turns text into Scenic code by retrieving and assembling snippets, and reports a collision rate 15 % above the strongest baselines [13]. LD-Scene has an LLM write a guidance loss; its adversarial levels weak, medium and strong give a time to collision of 2.06, 1.98 and 1.91 s, and the strong level's collision rate (39.33 %) is no higher than the medium level's (40.75 %) [76]. LangTraj trains text conditioning directly and reports a mADE of 2.29 against 2.65 without text and 2.70 for LLM-written guidance [73]. CaFe addresses a failure that other language-conditioned simulators may share: when instructions are broadcast, they change the behaviour of 82.7 % of nearby uninstructed agents at 8 s, while CaFe's private-stream design reduces this to 0.0 % and satisfies 40.8 % of timed clauses against 38.0 % without language [10]. Direct measurements of text-to-scenario adherence are rare in these rows; evidence is more often downstream, for example ego agents trained on generated scenes cutting the average collision rate from 0.08 to 0.035 on SafeBench [128].

### 3.4 Reward and return conditioning, reinforcement-learning fine-tuning and latent control

Reward tilting is a one-parameter control. In CtRL-Sim, tilting from -25 to 25 gives a relatively monotonic change in each metric, and at -25 the fine-tuned model produces 2.1 times the collisions and 1.8 times the off-road violations of the base model [25]; Scenario Dreamer reuses it and reports a planner collision rate of 4.9 % at kappa = +10 against 11.9 % at -50 [112]. A behaviour latent over four reward channels reaches positive controllability scores on all four channels (+0.66 safety, +0.61 map, +8.15 speed, +8.76 acceleration) [18]. Reinforcement-learning fine-tuning shows narrower demonstrations: failure rates of 0.226 (no-collision reward) and 0.136 (no-off-road reward) against 0.483 and 0.450 without it [17]; goal reach rising from 35.37 % to 50.00 % [105]. Latent control is shown by moving the minimum short-term time to collision from 3.263 to 1.967 between nominal and challenging labels [15].

### 3.5 Many "controllable" generators steer an adversarial objective, not an attribute

Of the 11 papers in the "other" family, most search or optimise for collisions against a system under test: KING reaches a collision rate of 82.50 % against 68.33 % for CMA-ES [72], CAT lowers an end-to-end policy's crash rate from 19.89 % to 13.43 % in log replay [11], and AdvSim reports an average collision rate of 32.8 % [3]. This is a purpose, adversarial testing and training, rather than a user-facing control, and it explains why evidence of control is often a downstream safety number.

### 3.6 What the scenario-level evidence does not show

The rows report different metrics on different data and baselines, with some shared setups, so this review does not rank methods. Several papers state that they model vehicles only [60][111], a few labelled as controllable are, by their own notes, realism simulators or adversarial pipelines [4][8][39], and several controls are shown only qualitatively [130][9].

## 4. World models for driving

### 4.1 Control interfaces

At the sensor level the signal is usually geometric. Sixteen of the 64 papers condition on layouts, boxes, maps or BEV sketches; 19 on ego action or trajectory; 16 combine several. MagicDrive takes camera pose, a BEV road map, 3D boxes and text [81]; MagicDrive-V2 extends this to up to 241 frames from six cameras [80]; GAIA-2 conditions on ego speed and curvature, 3D boxes of dynamic agents, metadata such as country, weather and time of day, and text or image embeddings [55]. Vista offers a unified action interface (commands, goal points, trajectories, steering and speed) learned in a second phase over frozen weights [137]. Language enters through an LLM that writes trajectory scripts or edits a scene: DriveDreamer-2 uses a fine-tuned GPT-3.5 to produce trajectories that become an HD map and 3D boxes before the video model [35], and ChatSim uses GPT-4 agents on a reconstructed scene, which its own notes say is not a learned generative world model [48]. Only one tabled paper makes a risk level the signal, and its main claim of matching the target risk is reported without the analysis [104].

### 4.2 Evidence of control is mostly indirect

The rows rarely report an action-following measurement. Where they do, the numbers are favourable: Vista's average FVD on nuScenes falls from 367.2 without actions to 207.6 with a trajectory [137]; ReSim's zero-shot trajectory difference on Waymo is 1.13 against 5.68 for Vista without action [103]; GeoDrive's trajectory error is 1.62 against 2.77 for Vista (units of 10^-2) [59]; OmniNWM's translation error is 1.18 m against 7.56 m for UniScene [90]; MyGo reports camera-control errors on RealEstate10K, since COLMAP fails on dynamic nuScenes scenes [85]. For layout control, the measure is usually how much perception performance drops on generated images: DrivingDiffusion's road mIoU is 63.2 (-8.1 %) and vehicle mIoU 31.6 (-4.4 %) against baseline 71.3 and 36.0 [43]; DriveScape reports -9.25 and -5.98 mIoU for road and vehicle [38]; Panacea's NDS on generated validation data is 32.1 against 46.9 on real data [92].

For many papers the evidence is downstream or qualitative: GAIA-1's controllability evidence is qualitative [54]; BEVWorld's action control is shown in a figure [7]; DriveDreamer's synthetic data raises BEVFusion mAP from 32.8 to 35.8 [37]; Cosmos-Drive-Dreams gains 6.0 % in lane detection at 2,000 real clips, up to 9.4 % in fog [21].

### 4.3 Four analyses suggest that action conditioning is weaker than it looks

Four of the tabled papers study control itself, and they point the same way. On Cityscapes the executed action adds at most 2.46 mid-term mIoU to a semantic forecaster [31]. Released plan-conditioned world models reach at most about a third of the real-video scene response under speed plans, and a training-free retiming wrapper reaches 0.93 to 1.04 of the real stereo response for a 0.54 m shift [42]. An energy guidance method brings a planned trajectory to a mean of 1.3 m from a braking target against 13.6 m unguided, but video optical flow changes by 2 % or less, so control acts on the trajectory more than on the video [70]. A training-free counterfactual pipeline raises a measure of faithfulness (RecD/RecC) from 0.38/0.33 to 0.70/0.65 on Vista [65]. These papers support the concern that a world model can look controllable without the video responding to the plan; they do not show it for every model.

### 4.4 Closed-loop use is shown, but thinly

Eight of the 64 rows say the model was run in a closed loop with a policy: DriveArena [34], DrivingSphere [45], HelloWorld [63], Making the World React Realistically [82], OmniDreams [86], OmniNWM [90], ReSim [103] and X-World [140]. Two more feed planning back into the loop [41][40]. Three of the eight are qualitative demonstrations [63][103][140]. The quantitative ones are modest or specific: UniAD driving through DriveArena completes on average 0.137 of the route (ADS 0.086) [34], and through DrivingSphere 0.1170 (ADS 0.0851) [45]; OmniNWM reports a best scenario pass rate of 87.3 % on 150 nuScenes validation scenes at 12 Hz [90]; OmniDreams runs 20 s rollouts with replanning every 533 ms [86]. The remaining 54 rows report open-loop generation or prediction.

### 4.5 Bridging the two layers

Several papers connect scenario-level control to sensor-level rendering. DriveDreamer-2 turns text into agent trajectories and then into HD maps and boxes [35]; a risk-controllable multi-view diffusion model produces agent trajectories first and conditions the video on them [104]; TeraSim-World composes behaviour models, an adversity orchestrator and rendered HD-map videos for a video model [124]; BehaviorWorldGen generates behaviour variants that are used to improve action models [5]. This layered design lets control live in a compact representation, but none of these rows shows a quantitative check that the rendered video preserves the specified behaviour.

## 5. What companies say

Company statements are claims from marketing and technical pages; the grades A and B separate those with a described method or number from those with product wording.

**World models are replacing reconstruction-based simulation in several companies.** Waymo says purely reconstructive methods such as 3D Gaussian splats suffer visual breakdowns when the route differs from the logged one [W4], and XPeng says reconstruction-based simulation struggles beyond the reconstructed range [X2]. NVIDIA's OmniDreams paper contrasts itself with reconstruction-based neural simulators that are constrained by their initial captured data [N8]. Applied Intuition's Neural Sim, announced in January 2025, still turns drive logs into closed-loop sensor simulation [A1][A2].

**The base is a large pretrained model.** The Waymo World Model is built on Genie 3 [W1]; XPeng's X-World on the video model WAN 2.2 [X1]; OmniDreams on Cosmos, with 21k hours of driving data in mid- and post-training [N7][N9]; Wayve's GAIA-2 is a latent diffusion world model [Y1].

**Control comes through familiar interfaces.** Waymo names driving action, scene layout and language control [W3][W2]; Wayve conditions on ego dynamics, agent configurations, environmental factors and road semantics [Y2]; XPeng on ego actions, traffic participants and static road elements [X5]; NVIDIA's Cosmos Transfer varies weather, lighting and terrain of an existing scenario [N3]. These mirror the academic interfaces in section 4; the public statements give few control measurements.

**The use is closed-loop evaluation and training.** OmniDreams is described as a reactive environment with the Alpamayo 1 policy and AlpaSim, and a world-action model post-trained from it is reported, preliminarily, to surpass a vision-language-action research policy using one fifth of the parameters [N8][N10]. Tesla describes a neural world simulator that predicts the next sensor state from the current state and next action, connected to the policy to evaluate it, and says it can create adversarial scenarios, without method or numbers [T1][T2][T3]. Huawei lists a cloud world engine and an in-vehicle world action model, with multi-agent game theory and online reinforcement learning on the cloud side [H1][H2]; its own page says the passenger-car system is an assisted-driving feature [H3]. XPeng says its simulation scenarios grew from 30,000 to more than 500,000 in a year [X4].

**Failure discovery is part of generation.** Mobileye pairs a multi-agent data analyst that finds recurring failures with a targeted scenario simulator, and says generated data should extend, not replace, real data [M1][M2][M3]. NVIDIA and Alpamayo position reasoning vision-language-action models as teachers to distil, not in-car models [N5], and release models, a simulator and datasets openly [N4][N6].

What is missing. Waymo, Tesla and XPeng describe closed systems and publish few measurements of controllability. Wayve's own GAIA-3 pages answered HTTP 403, Zoox's pages could not be read, and no company statement was found for Li Auto, so those are absent from this evidence. A Baidu launch is only available through a secondary page [D1] and is not used as evidence. Waabi's generative-simulator statement is from 2022 [B1][B2].

## 6. Cross-cutting findings

1. **Control is seldom measured directly.** At both layers the common evidence is a downstream or fidelity number (collision rate against a baseline, perception on generated data, FID and FVD) rather than a measurement of whether the output follows the specified signal. Exceptions exist (sections 3.1 and 4.2) and the four analyses in section 4.3 show why the distinction matters.
2. **A knob that moves a metric and a knob that moves the world are different.** Guidance papers pay for the dial in realism [107][98]; the energy-guidance paper shows a trajectory moving while video barely changes [70].
3. **Much "control" at the scenario level is an objective.** Adversarial purpose dominates among the papers labelled controllable (section 3.5), and many reported benefits are for the planner trained on the data, not for the user who specifies the scenario.
4. **Language control is a mixture of three designs.** Text can be turned into code or a loss [13][76], trained in directly [73][10], or used to edit a scene [48]; their failure modes differ, and reliability is rarely measured directly.
5. **Closed-loop use is the direction of travel but the evidence is thin.** Both the company statements and the academic rows point to closed-loop evaluation and training, yet only eight of 64 world-model rows run a closed loop and three of those are qualitative.
6. **No shared yardstick.** The rows use different data, metrics and baselines, with only a few shared setups, so this survey does not rank methods.

## 7. Open problems and research directions (my proposals, not findings)

Each direction names the gap in the evidence it comes from, a first experiment, and what would count as success. They are proposals for discussion and have not been tested.

1. **Measure control, not just fidelity.** Gap: sections 4.2 and 4.3. Proposal: a small benchmark for world models and scenario generators that scores whether the output follows a specified signal (action following, layout adherence, risk level) with the same protocol at both layers, including a probe like the shuffled-action test in [31]. Success: methods that look equal on FID and FVD separate on the control score, and the ranking is stable across seeds.
2. **Close the gap between the two layers.** Gap: section 4.5. Proposal: keep behaviour control in a compact scenario representation and test whether rendering preserves it, by extracting trajectories from generated video and comparing them with the specified ones. Success: a measured behaviour-preservation rate for a layered pipeline, compared with an end-to-end model.
3. **Check that closed-loop evaluation in a world model ranks policies as the real world does.** Gap: sections 4.4 and 5. The OmniDreams paper reports that the ranking of policies under a reconstruction-based simulator is preserved under its world model [86], but I found no independent check in the rows. Proposal: run several policies in a generative simulator and in a log-based or real evaluation and report the rank correlation, including cases where the world model's response to the plan is weak (section 4.3).
4. **Specify intent, not just objectives.** Gap: sections 3.3 and 3.5. Proposal: evaluate language-to-scenario adherence directly (does the generated scenario satisfy the clause, for the instructed and the uninstructed agents, as in [10]) instead of only downstream collision rates.
5. **Calibrated risk and style knobs across layers.** Gap: sections 3.1 and 3.4. Risk-level and percentile controls are measured well at the scenario level [99][66], reward tilting is a clean one-parameter dial [25][112], and one sensor-level paper has a risk signal [104]. Proposal: study where such knobs saturate or interact (for example extreme tilting giving implausible behaviour, as stated in [25]'s row) and test whether the same risk scale can drive both layers.
6. **Reproduction of reported control effects.** Gap: only a minority of rows state a code link in their packets, and a pilot ledger of 30 atomic claims from 6 papers has not been run. Proposal: register tolerances first and reproduce a few claims with public code (the ledger in this repository is built for that), starting with a guidance dial and a reward-tilting dial.
7. **Broader data and conditions.** Gap: the rows concentrate on a few public datasets (nuScenes, Waymo Open Motion and nuPlan appear throughout) and several papers say they model vehicles only [60][111]. Proposal: evaluate controllability on conditions the training data covers thinly (pedestrians, adverse weather, unusual road layouts) and report where control degrades.

## 8. Limits and how this was checked

- **Evidence base.** Rows come from partial packets; tables flattened by PDF extraction made some numbers uncertain, and these are noted in the rows. Neither table was read in full by a person. The first 34 scenario rows and the 43 added from chaining were audited on random samples (22 of 24 cells supported in each, 0 unsupported, the partial ones corrected); the world-model audit is reported in the repository notes.
- **Selection.** The screening decisions for chaining leads and for world-model candidates are mine, from titles and abstracts (some with no abstract), and are logged with reasons in the repository. The world-model papers were chosen partly by citation count, which favours older work; 40 in-scope world-model papers were deferred.
- **Company statements** are marketing and technical claims, are not independently verified, and cover only the companies named above.
- **Sentence check.** A second model, different from the one used for most of the extraction, checked every sentence of sections 1 to 6 against the table rows and company quotes cited; the process and outcome are in the repository.
- Section 7 is not checked against evidence: it is my reading of the gaps.
