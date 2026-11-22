# How controllability is achieved in driving scenario and traffic-simulation generation: a review of 34 papers

*Built only from comparison table B (`table.md`). Bracketed numbers refer to the reference list at the end. Every claim comes from a table row, which in turn comes from an evidence packet of that paper; nothing here was checked against full PDFs by a person. See "Validity".*

## 1. Scope

The corpus is 371 papers on traffic scenario generation and simulation, found with OpenAlex and arXiv searches limited to 2019 onward (a few records are older or undated, and 14 carry Crossref as a source), of which 288 had an open full text. From those I chose 34 from their abstracts to cover different control mechanisms, and filled one row each. Closed-access papers are absent by construction. The question is narrow: what does a user or designer specify, and how does that signal reach the generator?

## 2. A taxonomy by where the control signal enters

| Family (papers) | What is steered | How the signal is injected |
|---|---|---|
| Inference-time guidance (9): [1] [5] [12] [15] [20] [25] [26] [30] [34] | Differentiable or learned rules, costs and rewards: signal temporal logic rules [15], collision and off-road weights [5], adversarial objectives [1] [12] [26], pursuit costs [20], TTC weight [25], goals and soft constraints [34], reward functions derived from VLM proposals [30] | The gradient of an objective steers the denoising steps of a trained diffusion model, in [1] and [12] through a separately learned reward or objective model, in [20] optionally only in late reverse steps, and in [5] together with classifier-free guidance; [20] and [34] state that no retraining is needed. [30] uses gradient-free evolutionary guidance |
| Language / LLM-driven (5): [6] [10] [18] [19] [32] | A natural-language description of the scenario; for [32], a region choice plus a prompt | An LLM turns text into a symbolic intermediate: a loss function [10] [18] [19], or Scenic code snippets retrieved and assembled into a program [6]. [32] instead aligns an LLM to regional traffic and outputs text; its row shows no fine-grained steering in the packet |
| Conditioning inputs trained in (5): [13] [14] [27] [31] [33] | Agent attributes, map, goals, number of agents; for [14] also a trajectory sketch, a latent behaviour code or a language command | Cross-attention tokens [13] [27], adapters on a frozen backbone [14], hard endpoint constraints in infilling [31]. [33] is an imitative model whose row shows only partial control |
| Reward / return conditioning (3): [9] [11] [28] | A tilt coefficient per reward component [11], a single tilting strength on a collision-with-ego reward [28], or a behaviour latent over four reward channels [9] | The model predicts a return distribution that is tilted at sampling time [11] [28]; [9] feeds the latent as a cross-attention token with classifier-free guidance |
| RL fine-tuning (2): [8] [21] | Collision and off-road rewards [8]; per-agent goal points [21] | Policy-gradient fine-tuning of a diffusion model [8] or of a token model [21] |
| Latent-space control (2): [7] [16] | A discrete class or difficulty label | One designated latent dimension with a class prior [16]; a flow that transports latents from nominal to safety-critical [7] |
| Other (4): [2] [4] [17] [22] | An adversarial objective against a system under test [2] [4] [17]; behaviour tags for retrieval [22] | Black-box search [2], adversarial resampling of a motion predictor [4], gradient optimisation of adversarial actions through a differentiable bicycle model [17], retrieval-based in-context generation [22] |
| No control (4): [3] [23] [24] [29] | Nothing user-steerable | Simulators and sim-agent models without a user-steerable signal, kept for contrast and left out of the comparison below |

Some placements are judgement calls that the row notes flag: [28] mixes return tilting with scene-density conditioning, [14] uses trained adapters plus classifier-free guidance, and [30] feeds language-model proposals into guided diffusion.

## 3. What the rows show

### 3.1 Guidance gives a dial, at a price in realism

Nine papers are labelled inference-time guidance: eight steer a trained diffusion generator with a gradient and [30] with a gradient-free search. Gradient guidance of the sampling also appears in some language-driven rows and in [31]. The dial is shown with numbers in [25], [20] and [30], and as a trend in [12]. In [25], raising the TTC cost weight from 0.0 to 1.0 to 2.0 raises the collision rate from 48.2 to 53.6 to 60.7 %. In [20], raising the pursuit weight from 10 to 60 together with the step size from 0.05 to 0.10 lifts the ego-adversary collision rate from 18.9 % to 47.8 %, so the rise cannot be credited to the weight alone. In [30], lowering the social-constraint weight lambda from 1.0 to 0.3 raises the extrinsic reward by 86.49 %. In [12], the collision rate rises as the number of guided optimisation steps goes from 0 to 30, while naturalness metrics worsen.

The price is stated in several rows. Realism worsens slightly as the TTC weight rises in [25] (0.76 to 0.81, lower is better), and in [20] it worsens from 0.53 to 0.66 when the pursuit weight and step size are raised together. [20] also says guidance depends on differentiable, calibrated objectives, can degrade other fidelity metrics, adds compute and is sensitive to step size and weights.

### 3.2 Trained-in conditioning can be tested directly, but only for what was trained

[27] shows control of density: the agent-token match rate stays at 0.97 from 0 to 50 % masking, while the number of additionally generated agents rises from 0.4 to 12.6 as the mask probability rises. The paper varies the mask probability and infers from these counts that the global token controls density. [13] is mostly qualitative; the comparison its row reports with numbers (scenario collision rate 3.33 % against 13.59 % for a baseline) concerns interaction reasoning, and the packet shows no condition-adherence metric. [14] reports up to 83 % lower control error but evaluates with controls derived from ground-truth trajectories, and states that it controls a single agent and may favour control satisfaction over safe interaction when instructions conflict with traffic.

### 3.3 Reward tilting is a one-parameter control with a roughly monotone response

[11] tilts the return distribution with a coefficient between -25 and 25 and reports a relatively monotonic change in each metric; with the fine-tuned model at -25, collisions are 2.1 times and off-road violations 1.8 times those of the base model. [28] reuses it as a behaviour model, with planner collision at 4.9 % for kappa = +10 and 11.9 % for kappa = -50. [11] lists four limits: it controls behaviour but not initial placement, extreme tilting (-50) gives erratic, implausible behaviour, inference latency may make large-scale RL training expensive, and imitation drift can push agents off road. [9] steers a behaviour latent over four reward channels instead of one tilt per component, with positive controllability scores on all four channels (+0.66 safety, +0.61 map, +8.15 speed, +8.76 acceleration at guidance weight 1.5). It states that map steering depends on the reward definition (physical off-road and lane-centre measures fail to steer), and the table's notes add that its realism is mid-leaderboard, below non-controllable imitation models.

### 3.4 Language control passes through generated code, and some of the stated failures sit there

Four of the five language papers pass the text through a symbolic artefact. The stated failures of [10] and one of those of [19], that a wrong loss is neither detected nor repaired automatically, concern what the LLM writes. [19] has GPT-4 write a loss that guides each denoising step; besides the missing automatic detection and repair of a wrong loss, it cannot handle commands that depend heavily on the map, and takes about a minute per scenario. [10] has a refinement module that struggles when the LLM's first reading of the scenario is fundamentally wrong. In [18] the "strong" adversarial level gives a collision rate of 39.33 %, no higher than "medium" at 40.75 %, which the authors attribute to missed collision timing in low-speed interactions. [6] controls through Scenic code assembled from retrieved snippets, and the packet shows evaluation by adversarial strength and no text-fidelity metric.

### 3.5 Fine-tuning and latent control show narrow demonstrations

[8] cuts the failure rate to 0.226 under the no-collision reward and 0.136 under the no-off-road reward, from 0.483 and 0.450 without RL guidance, but only those two rewards are demonstrated, so the table's notes describe the control as essentially constraint satisfaction. [21] raises goal reach from 35.37 % to 50.00 % in one variant and states that its controllability is reasonable but imperfect. [16] is a two-page student abstract controlling a discrete class only. [7] moves minSTTC from 3.263 to 1.967 and the near-miss rate from 0.281 to 0.500 between the nominal and challenging labels, and states that it controls the degree of criticality, not the specific manoeuvre.

## 4. Cross-cutting observations

1. **Safety-critical generation is a frequent steered quantity.** At least 11 of the 30 papers with any control steer collisions or adversarial strength: [1] [2] [4] [6] [12] [17] [18] [20] [25] [26] [30]. This partly reflects how I chose the 34 from abstracts, so it describes this sample, not the field.
2. **Demonstrated control is often narrow.** Collision and off-road rewards [8], goal points [21], a discrete class [16], the degree of criticality [7], behaviour but not placement [11]; [14] controls a single agent. Some rows show wider signals: four reward channels [9] and six temporal-logic rules [15].
3. **Evidence is hard to compare across papers.** The rows report collision rate, adversarial collision, goal reach, token match rate, control error and human preference, mostly on different data and with different baselines; a few share a setup, for example [15] and [19] both report failure rate and rule violation on nuScenes validation scenes. I make no ranking.
4. **Evidence quality varies.** Qualitative for [13] and [34]; oracle controls for [14]; human preference for [22]; and in 7 of 34 rows the packet showed no stated limitations.

## 5. Gaps that the rows support

- No row shows a shared controllability benchmark: the rows report different metrics on different data, although [6] and [32] both evaluate on SafeBench.
- Several models cover vehicles only: [15] and [27] say only vehicles are modelled, and [4] says only its adversarial agents are vehicles (no pedestrians or cyclists).
- [14] states that it controls a single agent and may favour control satisfaction over safe interaction when instructions conflict with traffic.
- For the language papers that go through code or a loss function, reliability depends on what the LLM writes [19] [10] (section 3.4); [32] outputs text only.
- For reward tilting, the open items stated in [11] are placement control, extreme tilt, inference latency and imitation drift; [9], which conditions on a behaviour latent rather than tilting, states that map controllability depends on the reward definition and that guardrails degrade at larger steering strength.

## 6. Validity

- **Packets are partial.** Each row came from the first two pages plus the best passages per field, not the whole paper. "Not stated in packet" does not mean the paper omits it. Several rows record missing tables (for example guided results in [1], success rates in [10]).
- **Rows were filled by Claude sub-agents,** not by a person. Automated checks confirmed the schema, pages, and that numbers occur in the packet; that check is weak for short numbers.
- **Independent audit of a random sample.** A separate sub-agent checked 24 cells (control mechanism and evidence for 12 randomly chosen papers) against the packets: 22 supported, 2 partial, 0 unsupported, no page mismatches. The two partial cells were an inferred phrase in [17] and a "not stated" in [3] that the packet did in fact answer; both were corrected. This is a sample of 24 of 238 cells, so it bounds the error rate loosely; the other fields (data, metrics, limitations) were not audited.
- **Selection.** I chose the 34 papers from abstracts; family labels are judgement calls; open-access papers only; one search pipeline (OpenAlex and arXiv), with 15 of 16 known probe papers recovered.
- **Sentence-by-sentence check against the table.** A model different from the session's (an opus sub-agent, run in four parts) checked each sentence of sections 1 to 5 against the table rows it cites. First pass on the earlier text: 49 claims, 26 supported, 19 partial, 1 unsupported, 3 not checkable. I revised the text for the flagged points and a second pass gave 52 claims, 39 supported, 10 partial, 0 unsupported, 3 not checkable. I revised again and the 14 changed sentences were checked once more: 12 supported, 2 partial. Those two were then reworded, and the final rewording was not checked again. The three not-checkable sentences state the review's question, its selection from abstracts and the absence of a ranking. A pass finds new issues in text it has already seen, so "supported" means supported by the table rows, not that the table is right.
- **Not done:** no person has read the PDFs, so rows, table and review all rest on partial evidence packets read by models.

## References

Authors, years, venues and DOIs come from the search metadata (OpenAlex, arXiv, Crossref) and were not checked by hand. Surnames are taken by a simple rule and can be wrong for some names; the venue field sometimes shows the preprint server even when a published version exists; a blank DOI means the metadata had none. Check before citing.

1. Xie, Guo, Wang et al. (2024). AdvDiffuser: Generating Adversarial Safety-Critical Driving Scenarios via Guided Diffusion. arXiv.
2. Wang, Pun, Tu et al. (2021). AdvSim: Generating Safety-Critical Scenarios for Self-Driving Vehicles. arXiv. https://doi.org/10.1109/cvpr46437.2021.00978
3. Zhou, Hu, Chen et al. (2024). BehaviorGPT: Smart Agent Simulation for Autonomous Driving with Next-Patch Prediction. neural information processing systems. https://doi.org/10.52202/079017-2527
4. Zhang, Peng, Li et al. (2023). CAT: Closed-loop Adversarial Training for Safe End-to-End Driving. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2310.12432
5. Lin, Huang, Phan et al. (2025). Causal Composition Diffusion Model for Closed-loop Traffic Generation. IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings - IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings. https://doi.org/10.1109/cvpr52734.2025.02565
6. Zhang, Xu, Li (2024). ChatScene: Knowledge-Enabled Safety-Critical Scenario Generation for Autonomous Vehicles. IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings - IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings. https://doi.org/10.1109/cvpr52733.2024.01464
7. Gong, Zhang, Zhang et al. (2026). Conditional Flow-VAE for Safety-Critical Traffic Scenario Generation. arXiv.
8. Xiao, Erden, Wang (2025). Controllable Latent Diffusion for Traffic Simulation. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2503.11771
9. Lu, ZHU, Wang (2026). Controllable Sim Agents with Behavior Latents. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2607.02496
10. Liu, Li, Wang et al. (2025). Controllable Traffic Simulation through LLM-Guided Hierarchical Reasoning and Refinement. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/iros60139.2025.11247747
11. Rowe, Girgis, Gosselin et al. (2024). CtRL-Sim: Reactive and Controllable Driving Agents with Offline Reinforcement Learning. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2403.19918
12. Xu, Petiushko, Ding et al. (2025). DiffScene: Diffusion-Based Safety-Critical Scenario Generation for Autonomous Vehicles. Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v39i8.32951
13. Wang, Sun, Ma et al. (2024). DragTraffic: Interactive and Controllable Traffic Scene Generation for Autonomous Driving. 2024 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). https://doi.org/10.1109/iros58592.2024.10801623
14. Chen, Chang, Chen et al. (2026). ECoSim: Data Efficient Fine-Tuning for Controllable Traffic Simulation. Lecture notes in computer science. https://doi.org/10.1007/978-3-032-37196-6_2
15. Zhong, Rempe, Xu et al. (2023). Guided Conditional Diffusion for Controllable Traffic Simulation. Proceedings - IEEE International Conference on Robotics and Automation/Proceedings. https://doi.org/10.1109/icra48891.2023.10161463
16. Mammen, Kayatas, Wagner (2026). Guided Latent Spaces for Controllable Multi-Scenario Generation in Autonomous Driving (Student Abstract). Proceedings of the AAAI Conference on Artificial Intelligence. https://doi.org/10.1609/aaai.v40i48.42251
17. Hanselmann, Renz, Chitta et al. (2022). KING: Generating Safety-Critical Driving Scenarios for Robust Imitation via Kinematics Gradients. arXiv.
18. Peng, Xie, Guo et al. (2026). LD-scene: LLM-guided diffusion for controllable generation of adversarial safety-critical driving scenarios. Transportation Research Part C Emerging Technologies. https://doi.org/10.1016/j.trc.2026.105694
19. Zhong, Rempe, Chen et al. (2023). Language-Guided Traffic Simulation via Scene-Level Diffusion. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2306.06344
20. Phoolari, Kara, Lauer et al. (2026). Proposal-Conditioned Latent Diffusion for Closed-Loop Traffic Scenario Generation. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2606.27123
21. Ahmadi, Schofield, Khamidehi et al. (2026). RLFTSim: Realistic and Controllable Multi-Agent Traffic Simulation via Reinforcement Learning Fine-Tuning. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2605.19033
22. Ding, Cao, Zhao et al. (2024). RealGen: Retrieval Augmented Generation for Controllable Traffic Scenarios. Lecture notes in computer science. https://doi.org/10.1007/978-3-031-73033-7_6
23. Liu, Niedoba, Harvey et al. (2025). Rolling Ahead Diffusion for Traffic Scene Simulation. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2502.09587
24. Wu, Feng, Gao et al. (2024). SMART: Scalable Multi-agent Real-time Motion Generation via Next-token Prediction. neural information processing systems. https://doi.org/10.52202/079017-3622
25. Chang, Pittaluga, Tomizuka et al. (2024). SAFE-SIM: Safety-Critical Closed-Loop Traffic Simulation with Diffusion-Controllable Adversaries. Lecture notes in computer science. https://doi.org/10.1007/978-3-031-72664-4_14
26. Peng, Yao, Guo et al. (2025). Safety-Critical Traffic Simulation with Guided Latent Diffusion Model. IEEE International Conference on Intelligent Transportation Systems (ITSC). https://doi.org/10.1109/itsc60802.2025.11423275
27. Pronovost, Ganesina, Hendy et al. (2023). Scenario Diffusion: Controllable Driving Scenario Generation With Diffusion. Advances in Neural Information Processing Systems 36. https://doi.org/10.52202/075280-3014
28. Rowe, Girgis, Gosselin et al. (2025). Scenario Dreamer: Vectorized Latent Diffusion for Generating Driving Simulation Environments. IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings - IEEE Computer Society Conference on Computer Vision and Pattern Recognition/Proceedings. https://doi.org/10.1109/cvpr52734.2025.01604
29. Guo, Gao, Zhou et al. (2023). SceneDM: Scene-level Multi-agent Trajectory Generation with Consistent Diffusion Models. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2311.15736
30. Tian, Zhu, Zhang et al. (2026). SocialDriveGen: generating diverse traffic scenarios with controllable social interactions. Frontiers of Computer Science. https://doi.org/10.1007/s11704-026-51974-4
31. Lee, Pant, Fischmeister (2026). Top-down Traffic Scenario Generation via Joint Initial-Goal Diffusion and Trajectory Infilling. arXiv (Cornell University). https://doi.org/10.48550/arxiv.2608.11407
32. Tu, Niu, Zhang (2026). TrafficAlign: Aligning Large Language Models for Traffic Scenario Generation. Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), June 2026, pp. 39744-39754. https://doi.org/10.48550/arxiv.2606.29097
33. Philion, Peng, Fidler (2024). Trajeglish: Traffic Modeling as Next-Token Prediction. International Conference on Learning Representations. https://doi.org/10.48550/arxiv.2312.04535
34. Huang, Zhang, Vaidya et al. (2026). Versatile Behavior Diffusion for Generalized Traffic Agent Simulation. IEEE Transactions on Intelligent Transportation Systems. https://doi.org/10.1109/tits.2026.3662886
