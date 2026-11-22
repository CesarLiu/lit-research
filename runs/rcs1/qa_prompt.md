Answer the question below with the context.

Context:

pqac-e7c06534: CtRL-Sim controls agent behaviour by exponentially tilting the learned return distribution. For each reward dimension c a coefficient kappa_c is set (evaluated from -25 to 25); negative tilting yields worse-than-average behaviour, positive tilting better-than-average, and metrics change relatively monotonically with kappa. Fine-tuning on only 3500 CAT collision scenarios (30 minutes on one A100) strengthens adversarial behaviour: at -25 tilting the fine-tuned model produces 2.1x the collisions and 1.8x the offroad violations of the base model; at -10 it yields 238 more planner collisions over 1000 scenes. CAT makes more collisions but is not controllable and its agents are non-reactive.
From CtRL-Sim: Reactive and Controllable Driving Agents with Offline Reinforcement Learning doi:10.48550/arxiv.2403.19918

pqac-f3659242: Scenario Diffusion is a latent diffusion model whose controllability comes from conditioning. Map conditioning: a BEV map image is encoded and concatenated with the noisy sample along channels. Token conditioning: tokens enter the denoiser through cross-attention. Agent tokens are procedurally computed per agent (position, speed, length, motion profile). Partial tokenization with a mask probability p_mask lets the model generate agents without tokens. A global scene token encodes p_mask and controls the number of agents at inference; no agent tokens with p_mask=1 gives map-only generation.
From Scenario Diffusion: Controllable Driving Scenario Generation With Diffusion doi:10.52202/075280-3014

pqac-abc1357f: DragTraffic generates future trajectories conditioned on a context that can include vehicle type, length and width, starting position, speed and orientation, and target position, speed and orientation. For editing existing scenarios the target state is the condition; for new scenarios the initial agent states come from dragging, typing or an agent placement module. A MultiPath++ regression model gives an initial trajectory, and a conditional diffusion model refines it. CTG uses conditional diffusion for controllable simulation and CTG++ adds language instructions, but such methods need expert-designed constraints and loss functions.
From DragTraffic: Interactive and Controllable Traffic Scene Generation for Autonomous Driving doi:10.1109/iros58592.2024.10801623

pqac-8151e453: A guided VAE builds control into the latent space instead of external conditioning, which the authors say can distort the underlying probability distribution (critical for failure-probability estimation). One latent dimension encodes the scenario class: z=[z_type, z_rest], with a class-conditional prior N(z_type|mu_y, sigma_y^2) times N(z_rest|0,I) and an alignment loss pulling z_type to the class centre; total loss is reconstruction plus beta*KL plus alignment. Data: about 44,600 highway trajectories of six scenario types (cut-in, cut-out, cut-through, left and right). Validation classification error is at most 2e-2.
From Guided Latent Spaces for Controllable Multi-Scenario Generation in Autonomous Driving (Student Abstract) doi:10.1609/aaai.v40i48.42251

pqac-bea94318: DragTraffic is an instance-behaviour-level traffic scene generator aimed at high controllability. A regression model gives initial guesses, a symmetric hybrid expert (mixture of experts) architecture uses a separate model per agent type, and a conditional diffusion model, inspired by DragGAN, provides diversity and honours specified context: position, velocity, heading, length and width. Controls are applied by dragging or typing. The authors contrast this with CTG++, which needs repeated and complex training for different tasks, and claim the first interactive framework with this freedom for generating and editing traffic scenes.
From DragTraffic: Interactive and Controllable Traffic Scene Generation for Autonomous Driving doi:10.1109/iros58592.2024.10801623

Valid Keys: pqac-e7c06534, pqac-f3659242, pqac-abc1357f, pqac-8151e453, pqac-bea94318

---

Question: How is controllability achieved in driving scenario generation models?

Write an answer based on the context. If the context provides insufficient information reply "I cannot answer." For each part of your answer, indicate which sources most support it via citation keys at the end of sentences, like (pqac-e7c06534). Only cite from the context above and only use the citation keys from the context.

## Valid citation examples, only use comma/space delimited parentheticals:
- (pqac-d79ef6fa, pqac-0f650d59)
- (pqac-d79ef6fa)
## Invalid citation examples:
- (pqac-d79ef6fa and pqac-0f650d59)
- (pqac-d79ef6fa;pqac-0f650d59)
- (pqac-d79ef6fa-pqac-0f650d59)
- pqac-d79ef6fa and pqac-0f650d59
- Example's work (pqac-d79ef6fa)
- (pages pqac-d79ef6fa)
- Author et al. (2023)

Do not concatenate citation keys, just use them as is. Write in the style of a scientific article, with concise sentences and coherent paragraphs. This answer will be used directly, so do not add any extraneous information.

Answer (about 200 words, but can be longer):