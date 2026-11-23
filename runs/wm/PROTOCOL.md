# Survey: controllable scenario generation and world models for autonomous driving

Written 2026-11-22 BEFORE the world-model search. Report written from three evidence sets: (1) runs/tableC, 77 papers on scenario and traffic-simulation generation (trajectory level); (2) this run, driving world models (sensor level: video, occupancy, lidar), searched below; (3) runs/industry, company statements.

## Question
How is controllability achieved in driving world models (what does a user specify; how does it enter the model), how does it relate to controllable scenario generation, what do companies publicly say, and what is open?

## Inclusion for the world-model table
A method paper (2023 or later) that generates or predicts driving observations (multi-view video, occupancy, lidar, or latent states) or closed-loop interactive sensor-level simulation, with at least one control input (ego action or trajectory, layout, 3D boxes, HD map, text, scenario conditions). Excluded: surveys, benchmarks, datasets, pure perception or planning models that merely use a world-model idea without generating, scene reconstruction without generative control (3DGS/NeRF only), non-driving world models.
Open-access full text only. Selection from titles and abstracts, one recorded reason each.

## Probe list (from memory, before searching; a fair search should find these)
1. GAIA-1: A Generative World Model for Autonomous Driving
2. DriveDreamer: Towards Real-world-driven World Models for Autonomous Driving
3. MagicDrive: Street View Generation with Diverse 3D Geometry Control
4. Vista: A Generalizable Driving World Model with High Fidelity and Versatile Controllability
5. Driving into the Future: Multiview Visual Forecasting and Planning with World Model for Autonomous Driving
6. OccWorld: Learning a 3D Occupancy World Model for Autonomous Driving
7. Copilot4D: Learning Unsupervised World Models for Autonomous Driving via Discrete Diffusion
8. Panacea: Panoramic and Controllable Video Generation for Autonomous Driving
9. GenAD: Generalized Predictive Model for Autonomous Driving
10. DriveDreamer-2: LLM-Enhanced World Models for Diverse Driving Video Generation
11. LidarDM: Generative LiDAR Simulation in a Generated World
12. GAIA-2: A Controllable Multi-View Generative World Model for Autonomous Driving
13. WoVoGen: World Volume-aware Diffusion for Controllable Multi-camera Driving Scene Generation
14. DrivingDiffusion: Layout-Guided multi-view driving scene video generation with latent diffusion model
Recall = probes found in the merged results; the filter must not lose any.

## Procedure
fetch_papers (OpenAlex and arXiv, from 2023) -> merge_results with the same keyword rule family -> screen with reasons -> resolve_oa (+ arXiv title fallback) -> packets -> rows by sub-agents with the same schema -> assemble_table checks -> independent audit of a random sample.
