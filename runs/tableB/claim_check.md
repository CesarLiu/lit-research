# Claim check of the review

49 claims, 49 with a result. NOT-CHECKABLE 3, PARTIAL 19, SUPPORTED 26, UNSUPPORTED 1
Wrong citation reported for claims: none

## Not SUPPORTED
- **1 UNSUPPORTED** [1. Scope] The corpus is 371 papers from OpenAlex and arXiv (2019 onward) on traffic scenario generation and simulation, of which 288 had an open full text.
  - issue: 371 (candidates after keyword rule) and 288 (open full text retrieved) match PRISMA.md, but the sources 'OpenAlex and arXiv' and the year '2019 onward' appear nowhere in PRISMA.md.
- **4 NOT-CHECKABLE** [1. Scope] The question is narrow: what does a user or designer specify, and how does that signal reach the generator?
  - issue: Statement of the review's own research question; the table cannot confirm or deny it.
- **5 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: Inference-time guidance (9): [1] [5] [12] [15] [20] [25] [26] [30] [34] | Differentiable rules, costs or rewards: signal temporal logic rules [15], collision and off-road weights [5], adversarial objectives [1] [12] [26], pursuit costs [20], TTC weight [25] | Gradient of the objective perturbs each denoising step of a trained diffusion model; no retraining. [30] uses gradient-free evolutionary guidance
  - issue: Count 9 is correct, but 'perturbs each denoising step' loses [20]'s control_mechanism qualifier 'optionally in late reverse steps', and [1]/[12] guide with a separately learned reward/objective model (control_mechanism), which 'differentiable rules, costs or rewards' glosses over; [30]'s and [34]'s signals are not listed.
- **7 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: Conditioning inputs trained in (5): [13] [14] [27] [31] [33] | Agent attributes, map, goals, number of agents | Cross-attention tokens [13] [27], adapters on a frozen backbone [14], hard endpoint constraints in infilling [31]. [33] is an imitative model whose row shows only partial control
  - issue: Count 5 and mechanisms match, but the signal list 'agent attributes, map, goals, number of agents' omits [14]'s trajectory sketch, behaviour latent code and language command (control_signal).
- **8 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: Reward / return conditioning (3): [9] [11] [28] | A tilt coefficient per reward component [11] [28], or a behaviour latent over four reward channels [9] | The model predicts a return distribution that is tilted at sampling time [11] [28]; [9] feeds the latent as a cross-attention token with classifier-free guidance
  - issue: Count 3 is correct, but 'a tilt coefficient per reward component' fits [11] only; [28]'s control_signal is a single tilting strength on a collision-with-ego reward.
- **12 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: No control (4): [3] [23] [24] [29] | Nothing user-steerable | Realism-focused simulators that the search returned; excluded from the comparison below
  - issue: Count 4 is correct, but 'that the search returned' contradicts selection.txt, which says these four were chosen and 'kept for contrast'; [23]'s notes describe reactive, efficient simulation rather than realism; 'excluded from the comparison below' is a process statement the table cannot confirm.
- **14 PARTIAL** [3.1 Guidance gives a dial, at ] Nine papers steer a frozen generator with a gradient.
  - issue: Count 9 matches control_family 'inference-time guidance', but SocialDriveGen's control_mechanism is 'gradient-free evolutionary guidance' (8 use a gradient), other families (3 language rows, Top-down) also steer by gradient, and 'frozen' is stated in no guidance row.
- **15 PARTIAL** [3.1 Guidance gives a dial, at ] The dial is demonstrated numerically in three of them.
  - issue: Only true if SocialDriveGen is excluded (its controllability_evidence also gives numeric phi/lambda sweeps, making four of the nine), and DiffScene's evidence gives only a trend over N, no per-step numbers.
- **17 PARTIAL** [3.1 Guidance gives a dial, at ] In [20], raising the pursuit weight from 10 to 60 lifts ego collision from 18.9 % to 47.8 %.
  - issue: controllability_evidence says w_pursue 10 to 60 was raised together with step size eta 0.05 to 0.10, so the rise is not from the pursuit weight alone; the metric is ego-adversary collision.
- **20 PARTIAL** [3.1 Guidance gives a dial, at ] Realism worsens slightly as the TTC weight rises in [25] (0.76 to 0.81, lower is better) and as the pursuit weight rises in [20] (0.53 to 0.66).
  - issue: Numbers match (SAFE-SIM notes, [20] controllability_evidence), but 'slightly' is only in the SAFE-SIM row and [20] co-varied eta with w_pursue.
- **23 PARTIAL** [3.2 Trained-in conditioning gi] That is a direct test of the signal.
  - issue: Evaluative 'direct test' is not in the row; controllability_evidence varies mask probability and only infers that the global token controls density.
- **24 PARTIAL** [3.2 Trained-in conditioning gi] [13] is mostly qualitative; its one quantitative table concerns interaction reasoning, not condition adherence.
  - issue: 'Mostly qualitative' and interaction-reasoning SCR are in notes/controllability_evidence, but 'its one quantitative table' is not stated; metrics also list open-loop MinADE6/MinFDE6/heading/speed errors.
- **29 PARTIAL** [3.3 Reward tilting is a one-pa] [9] generalises from one tilt per reward component to a behaviour latent over four reward channels, reports positive controllability on all four, and notes that map steering fails with physical off-road and lane-centre definitions of the reward and that its realism is mid-leaderboard, below non-controllable imitation models.
  - issue: The mid-leaderboard realism remark comes from the row's notes field (annotator comment), not stated_limitations, yet the sentence says the paper notes it; 'positive on all four' ignores that unconditional CSM diagonals are also positive on three channels (controllability_evidence), and the 'generalises from one tilt per component' lineage is not in this row.
- **30 PARTIAL** [3.4 Language control is mediat] Four of the five language papers pass the text through a symbolic artefact, and their stated failures sit there.
  - issue: Count holds (5 language/LLM-driven rows in table.md; [19],[10],[18],[6] use code or Scenic), but stated failures sit in the code only for [19] and [10]; [18] and [6] have stated_limitations 'not stated in packet' and [18]'s strong-level anomaly is attributed to collision timing, not the code.
- **33 PARTIAL** [3.4 Language control is mediat] In [18] the "strong" adversarial level gives a collision rate of 39.33 %, no higher than "medium" at 40.75 %, which the authors attribute to missed collision timing.
  - issue: Numbers match the notes field, but the sentence drops the qualifier that the missed collision timing occurs in low-speed interactions (notes).
- **35 PARTIAL** [3.5 Fine-tuning and latent con] [8] cuts failure rates to 0.226 (collision) and 0.136 (off-road) from 0.483 and 0.450 without guidance, but only those two rewards are demonstrated, so its notes call the control essentially constraint satisfaction.
  - issue: Numbers and direction match controllability_evidence, but 'essentially constraint satisfaction' is the table annotator's notes-field judgement, presented as [8]'s own notes.
- **40 NOT-CHECKABLE** [4. Cross-cutting observations] This partly reflects how I chose the 34 from abstracts, so it describes this sample, not the field.
  - issue: selection.txt confirms 34 papers chosen from abstracts, but that this choice 'partly' explains safety-critical dominance is the author's interpretation (selection aim was mechanism spread, not safety), which the table cannot confirm.
- **41 PARTIAL** [4. Cross-cutting observations] **Demonstrated control is usually one or two objectives.** Collision and off-road [8], goals [21], a discrete class [16], criticality degree [7], one agent [14], behaviour but not placement [11].
  - issue: [14] 'one agent' is a count of agents, not objectives, and its control_signal lists sketch, latent code and language; [11] control_signal has three tilted reward components; 'usually' is not counted from the rows (e.g. [9] four channels, [15] six STL rules).
- **43 NOT-CHECKABLE** [4. Cross-cutting observations] I make no ranking.
  - issue: Statement of the author's own approach (no ranking); the table cannot confirm or deny it.
- **45 PARTIAL** [5. Gaps that the rows support] No row shows a shared controllability benchmark; each paper defines its own.
  - issue: No controllability benchmark appears in the rows ([1] stated_limitations notes none is accepted), but 'each paper defines its own' is overstated: datasets show [6] and [32] both use SafeBench, and [18]/[26] share the Adv-Ego collision metric with [25] as a baseline.
- **46 PARTIAL** [5. Gaps that the rows support] Several models cover vehicles only: [15], [27] and [4] say so.
  - issue: [15] and [27] stated_limitations say vehicles only, but [4] says only the adversarial agents are vehicles (no pedestrians or cyclists), which is narrower than the whole model covering vehicles only.
- **48 PARTIAL** [5. Gaps that the rows support] Reliability of language control depends on the code or loss that the LLM writes (section 3.4).
  - issue: Uncited; stated_limitations of [10] and [19] support dependence on LLM-written cost/loss code, but not all language control works that way ([14] trains a text encoder adapter, [32] outputs text descriptions, [6] retrieves Scenic snippets).
- **49 PARTIAL** [5. Gaps that the rows support] For reward tilting specifically, the open items stated are placement control and extreme tilt [11], and reward definitions that fail to steer [9].
  - issue: [9] control_mechanism is a return-inferred behaviour latent with classifier-free guidance, not reward tilting; and [11] stated_limitations also list inference latency and imitation drift, so 'the open items stated' is incomplete.

## Flagged automatically but judged SUPPORTED (second look)
- 2 no_citation :: From those I chose 34 from their abstracts to cover different control mechanisms, and filled one row
