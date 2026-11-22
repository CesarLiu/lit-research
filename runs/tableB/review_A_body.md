# How controllability is achieved in driving scenario and traffic-simulation generation: a review of 34 papers

*Built only from comparison table B (`table.md`). Bracketed numbers refer to the reference list at the end. Every claim comes from a table row, which in turn comes from an evidence packet of that paper; nothing here was checked against full PDFs by a person. See "Validity".*

## 1. Scope

The corpus is 371 papers from OpenAlex and arXiv (2019 onward) on traffic scenario generation and simulation, of which 288 had an open full text. From those I chose 34 from their abstracts to cover different control mechanisms, and filled one row each. Closed-access papers are absent by construction. The question is narrow: what does a user or designer specify, and how does that signal reach the generator?

## 2. A taxonomy by where the control signal enters

| Family (papers) | What is steered | How the signal is injected |
|---|---|---|
| Inference-time guidance (9): [1] [5] [12] [15] [20] [25] [26] [30] [34] | Differentiable rules, costs or rewards: signal temporal logic rules [15], collision and off-road weights [5], adversarial objectives [1] [12] [26], pursuit costs [20], TTC weight [25] | Gradient of the objective perturbs each denoising step of a trained diffusion model; no retraining. [30] uses gradient-free evolutionary guidance |
| Language / LLM-driven (5): [6] [10] [18] [19] [32] | A natural-language description of the scenario | An LLM turns text into a symbolic intermediate: a loss function [10] [18] [19] or a Scenic program [6]. [32] instead aligns an LLM to regional traffic and outputs text, with no fine-grained steering |
| Conditioning inputs trained in (5): [13] [14] [27] [31] [33] | Agent attributes, map, goals, number of agents | Cross-attention tokens [13] [27], adapters on a frozen backbone [14], hard endpoint constraints in infilling [31]. [33] is an imitative model whose row shows only partial control |
| Reward / return conditioning (3): [9] [11] [28] | A tilt coefficient per reward component [11] [28], or a behaviour latent over four reward channels [9] | The model predicts a return distribution that is tilted at sampling time [11] [28]; [9] feeds the latent as a cross-attention token with classifier-free guidance |
| RL fine-tuning (2): [8] [21] | Collision and off-road rewards [8]; per-agent goal points [21] | Policy-gradient fine-tuning of a diffusion model [8] or of a token model [21] |
| Latent-space control (2): [7] [16] | A discrete class or difficulty label | One designated latent dimension with a class prior [16]; a flow that transports latents from nominal to safety-critical [7] |
| Other (4): [2] [4] [17] [22] | An adversarial objective against a system under test [2] [4] [17]; behaviour tags for retrieval [22] | Black-box search [2], adversarial resampling of a motion predictor [4], gradient optimisation of adversarial actions through a differentiable bicycle model [17], retrieval-based in-context generation [22] |
| No control (4): [3] [23] [24] [29] | Nothing user-steerable | Realism-focused simulators that the search returned; excluded from the comparison below |

Some placements are judgement calls that the row notes flag: [28] mixes return tilting with scene-density conditioning, [14] uses trained adapters plus classifier-free guidance, and [30] feeds language-model proposals into guided diffusion.

## 3. What the rows show

### 3.1 Guidance gives a dial, at a price in realism

Nine papers steer a frozen generator with a gradient. The dial is demonstrated numerically in three of them. In [25], raising the TTC cost weight from 0.0 to 1.0 to 2.0 raises the collision rate from 48.2 to 53.6 to 60.7 %. In [20], raising the pursuit weight from 10 to 60 lifts ego collision from 18.9 % to 47.8 %. In [12], the collision rate rises as the number of guided optimisation steps goes from 0 to 30, while naturalness metrics worsen.

The price is stated in several rows. Realism worsens slightly as the TTC weight rises in [25] (0.76 to 0.81, lower is better) and as the pursuit weight rises in [20] (0.53 to 0.66). [20] also says guidance depends on differentiable, calibrated objectives, can degrade other fidelity metrics, adds compute and is sensitive to step size and weights.

### 3.2 Trained-in conditioning gives the cleanest evidence, but only for what was trained

[27] shows control of density: the agent-token match rate stays at 0.97 from 0 to 50 % masking, while the number of additionally generated agents rises from 0.4 to 12.6 as the mask probability rises. That is a direct test of the signal. [13] is mostly qualitative; its one quantitative table concerns interaction reasoning, not condition adherence. [14] reports up to 83 % lower control error but evaluates with controls derived from ground-truth trajectories, and states that it controls a single agent and may favour control satisfaction over safe interaction.

### 3.3 Reward tilting is a one-parameter control with a monotone response

[11] tilts the return distribution with a coefficient between -25 and 25 and reports a relatively monotonic change in each metric; with the fine-tuned model at -25, collisions are 2.1 times and off-road violations 1.8 times those of the base model. [28] reuses it as a behaviour model, with planner collision at 4.9 % for kappa = +10 and 11.9 % for kappa = -50. [11] states two limits: it controls behaviour but not initial placement, and extreme tilting (-50) gives erratic, implausible behaviour. [9] generalises from one tilt per reward component to a behaviour latent over four reward channels, reports positive controllability on all four, and notes that map steering fails with physical off-road and lane-centre definitions of the reward and that its realism is mid-leaderboard, below non-controllable imitation models.

### 3.4 Language control is mediated by generated code, and that is where it fails

Four of the five language papers pass the text through a symbolic artefact, and their stated failures sit there. [19] has GPT-4 write a loss that guides each denoising step; it cannot detect or repair a wrong loss, cannot handle commands that depend heavily on the map, and takes about a minute per scenario. [10] has a refinement module that struggles when the LLM's first reading of the scenario is fundamentally wrong. In [18] the "strong" adversarial level gives a collision rate of 39.33 %, no higher than "medium" at 40.75 %, which the authors attribute to missed collision timing. [6] controls through Scenic code and is evaluated by adversarial strength rather than by text fidelity.

### 3.5 Fine-tuning and latent control show narrow demonstrations

[8] cuts failure rates to 0.226 (collision) and 0.136 (off-road) from 0.483 and 0.450 without guidance, but only those two rewards are demonstrated, so its notes call the control essentially constraint satisfaction. [21] raises goal reach from 35.37 % to 50.00 % in one variant and states that its controllability is reasonable but imperfect. [16] is a two-page student abstract controlling a discrete class only. [7] moves minSTTC from 3.263 to 1.967 and the near-miss rate from 0.281 to 0.500 between the nominal and challenging labels, and states that it controls the degree of criticality, not the specific manoeuvre.

## 4. Cross-cutting observations

1. **Safety-critical generation dominates the steered quantity.** At least 11 of the 30 papers with any control steer collisions or adversarial strength: [1] [2] [4] [6] [12] [17] [18] [20] [25] [26] [30]. This partly reflects how I chose the 34 from abstracts, so it describes this sample, not the field.
2. **Demonstrated control is usually one or two objectives.** Collision and off-road [8], goals [21], a discrete class [16], criticality degree [7], one agent [14], behaviour but not placement [11].
3. **Evidence is not comparable across papers.** The rows report collision rate, adversarial collision, goal reach, token match rate, control error and human preference, on different data and with different baselines. I make no ranking.
4. **Evidence quality varies.** Qualitative for [13] and [34]; oracle controls for [14]; human preference for [22]; and in 7 of 34 rows the packet showed no stated limitations.

## 5. Gaps that the rows support

- No row shows a shared controllability benchmark; each paper defines its own.
- Several models cover vehicles only: [15], [27] and [4] say so.
- [14] states that it controls a single agent and may favour control satisfaction over safe interaction when instructions conflict with traffic.
- Reliability of language control depends on the code or loss that the LLM writes (section 3.4).
- For reward tilting specifically, the open items stated are placement control and extreme tilt [11], and reward definitions that fail to steer [9].

## 6. Validity

- **Packets are partial.** Each row came from the first two pages plus the best passages per field, not the whole paper. "Not stated in packet" does not mean the paper omits it. Several rows record missing tables (for example guided results in [1], success rates in [10]).
- **Rows were filled by Claude sub-agents,** not by a person. Automated checks confirmed the schema, pages, and that numbers occur in the packet; that check is weak for short numbers.
- **Independent audit of a random sample.** A separate sub-agent checked 24 cells (control mechanism and evidence for 12 randomly chosen papers) against the packets: 22 supported, 2 partial, 0 unsupported, no page mismatches. The two partial cells were an inferred phrase in [17] and a "not stated" in [3] that the packet did in fact answer; both were corrected. This is a sample of 24 of 238 cells, so it bounds the error rate loosely; the other fields (data, metrics, limitations) were not audited.
- **Selection.** I chose the 34 papers from abstracts; family labels are judgement calls; open-access papers only; one search pipeline (OpenAlex and arXiv), with 15 of 16 known probe papers recovered.
- **Not done:** no person has read the PDFs; no citation-by-citation grounding of each sentence in this review beyond the table rows.
