# Claim check of the review

52 claims, 52 with a result. NOT-CHECKABLE 3, PARTIAL 10, SUPPORTED 39
Wrong citation reported for claims: none

## Not SUPPORTED
- **4 NOT-CHECKABLE** [1. Scope] The question is narrow: what does a user or designer specify, and how does that signal reach the generator?
  - issue: Statement of the review's framing question; the table can neither confirm nor deny it.
- **5 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: Inference-time guidance (9): [1] [5] [12] [15] [20] [25] [26] [30] [34] | Differentiable or learned rules, costs and rewards: signal temporal logic rules [15], collision and off-road weights [5], adversarial objectives [1] [12] [26], pursuit costs [20], TTC weight [25], goals and soft constraints [34], VLM-written reward functions [30] | The gradient of an objective steers the denoising steps of a trained diffusion model, in [1] and [12] through a separately learned reward or objective model and in [20] optionally only in late reverse steps; no retraining. [30] uses gradient-free evolutionary guidance
  - issue: [30] control_signal/base_model say VLM proposals are turned into rewards by an LLM, not 'VLM-written reward functions'; 'no retraining' is stated only in [20] and [34] control_mechanism/control_signal, while [5] also uses classifier-free guidance and [1]/[12] train a separate reward/objective model.
- **6 PARTIAL** [2. A taxonomy by where the con] TABLE ROW: Language / LLM-driven (5): [6] [10] [18] [19] [32] | A natural-language description of the scenario | An LLM turns text into a symbolic intermediate: a loss function [10] [18] [19] or a Scenic program [6]. [32] instead aligns an LLM to regional traffic and outputs text, with no fine-grained steering
  - issue: [6] control_mechanism builds the Scenic program by retrieving and assembling stored snippets, not by the LLM writing it; [32] control_signal is a region choice plus prompt, not a scenario description, and 'no fine-grained steering' drops the row's qualifier 'shown in packet'.
- **14 PARTIAL** [3.1 Guidance gives a dial, at ] Nine papers steer a trained diffusion generator by guidance at sampling time: eight with a gradient and [30] with a gradient-free search.
  - issue: Recount gives 9 rows with control_family 'inference-time guidance' (8 gradient, SocialDriveGen [30] gradient-free), but control_mechanism of three language/LLM-driven rows (CTG++, LLM-guided hierarchical reasoning, LD-Scene) and the Top-down infilling row also steer diffusion sampling by gradient guidance, so 'nine papers' is the family count, not all papers doing this.
- **25 PARTIAL** [3.2 Trained-in conditioning ca] [13] is mostly qualitative; its quantitative comparison (scenario collision rate 3.33 % against 13.59 % for a baseline) concerns interaction reasoning, and no condition-adherence metric is reported.
  - issue: Row notes say no condition-adherence metric 'in the packet', a qualifier the sentence drops; metrics field also lists open-loop MinADE6, MinFDE6, heading and speed error, so SCR is not shown to be its only quantitative comparison.
- **32 PARTIAL** [3.4 Language control passes th] Four of the five language papers pass the text through a symbolic artefact, and the stated failures of [19] and [10] sit there.
  - issue: Count of 4 of 5 language/LLM-driven papers using a symbolic artefact checks out (TrafficAlign outputs text descriptions), but only one of [19]'s three stated_limitations (wrong loss code) sits in the generated code; heavy-map commands and the 1-minute runtime do not, so 'the stated failures of [19] sit there' overgeneralises.
- **36 PARTIAL** [3.4 Language control passes th] [6] controls through Scenic code and is evaluated by adversarial strength rather than by text fidelity.
  - issue: The notes say only that no text-to-code accuracy metric appears in the packet; the sentence drops the 'in packet' qualifier and states as fact that the paper is not evaluated by text fidelity.
- **37 PARTIAL** [3.5 Fine-tuning and latent con] [8] cuts failure rates to 0.226 (collision) and 0.136 (off-road) from 0.483 and 0.450 without guidance, but only those two rewards are demonstrated, so the table's notes describe the control as essentially constraint satisfaction.
  - issue: In controllability_evidence, 0.226 and 0.136 are overall failure rates (collision or off-road) under the no-collision and no-off-road rewards; labelling them '(collision)' and '(off-road)' reads as per-type rates, which the notes flag as ambiguous.
- **41 PARTIAL** [4. Cross-cutting observations] **Safety-critical generation dominates the steered quantity.** At least 11 of the 30 papers with any control steer collisions or adversarial strength: [1] [2] [4] [6] [12] [17] [18] [20] [25] [26] [30].
  - issue: The count holds (34 rows minus 4 'none/uncontrolled' = 30; all 11 cited rows steer collisions or adversarial strength in control_signal/controllability_evidence), but 11 of 30 is a minority, so 'dominates' is the sentence's own strength, not the rows'; it would only hold under a broader count that also includes rows such as [11], CCDiff, Scenario Dreamer and [34].
- **42 NOT-CHECKABLE** [4. Cross-cutting observations] This partly reflects how I chose the 34 from abstracts, so it describes this sample, not the field.
  - issue: selection.txt confirms the 34 were chosen from abstracts (aim: cover different control mechanisms), but the causal claim that this 'partly' explains the safety-critical share is the author's interpretation and the table cannot confirm or deny it.
- **45 PARTIAL** [4. Cross-cutting observations] **Evidence is not comparable across papers.** The rows report collision rate, adversarial collision, goal reach, token match rate, control error and human preference, on different data and with different baselines.
  - issue: All six listed metric types appear in the metrics/evidence fields, but the blanket 'not comparable across papers' goes beyond the rows: [15] and [19] share nuScenes, 100 validation scenes, failure rate and rule violation, and [18] reports Adv-Ego collision against Safe-Sim (datasets/metrics fields).
- **46 NOT-CHECKABLE** [4. Cross-cutting observations] I make no ranking.
  - issue: A statement about the author's own process (no ranking); the table cannot confirm or deny it.
- **52 PARTIAL** [5. Gaps that the rows support] For reward tilting, the open items stated in [11] are placement control, extreme tilt, inference latency and imitation drift; for the behaviour-latent variant [9], reward definitions that fail to steer.
  - issue: The four [11] items match stated_limitations, but for [9] the row says only the map channel's controllability depends on the reward definition (off-road and lane-centerline rewards fail to steer); the sentence drops this map-only qualifier and the guardrail-degradation limit.

## Flagged automatically but judged SUPPORTED (second look)
- 1 number_not_in_cited_rows 2019; number_not_in_cited_rows 288; number_not_in_cited_rows 371; no_citation :: The corpus is 371 papers on traffic scenario generation and simulation, found with OpenAlex and arXi
- 2 no_citation :: From those I chose 34 from their abstracts to cover different control mechanisms, and filled one row
- 51 number_not_in_cited_rows 3.4 :: For the language papers that go through code or a loss function, reliability depends on what the LLM
