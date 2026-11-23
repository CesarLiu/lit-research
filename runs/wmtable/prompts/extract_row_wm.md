You are filling one row of a comparison table per paper, about HOW CONTROLLABILITY IS ACHIEVED in driving WORLD MODELS and sensor-level driving scene generators (multi-view video, occupancy, lidar, 4D scenes).

Input: the list of paper ids in {GROUP_FILE} (one id per line). For each id, read the evidence packet {RUN_DIR}\packets\<id>.md. A packet holds the paper's first two pages plus the best passages from the paper for five topics. Passages are labelled [pages X-Y].

Output: for each id, write {RUN_DIR}\rows\<id>.json containing exactly this JSON object (valid JSON, UTF-8):
{
 "id": "<id>",
 "title": "<paper title from the packet>",
 "control_family": one of "action or trajectory conditioning" | "layout, box, map or BEV conditioning" | "text or language conditioning" | "multi-condition unified control" | "scenario, risk or event conditioning" | "camera or viewpoint control" | "inference-time guidance or editing" | "prediction without a control input" | "other" | "not stated in packet",
 "output_modality": {"value": "what is generated or predicted: multi-view video, single-view video, occupancy, lidar, camera plus lidar, 3D or 4D scene, other", "pages": ""},
 "control_signal":  {"value": "what a user or designer specifies to steer generation (ego action or trajectory, layout, 3D boxes, HD map, text, camera pose, scenario or risk condition...)", "pages": "e.g. 3-4"},
 "control_mechanism": {"value": "how that signal is injected (e.g. ControlNet branch, cross-attention, channel concatenation, token conditioning, guidance at sampling, fine-tuning)", "pages": ""},
 "base_model": {"value": "model family and key components, including any pretrained video or image backbone", "pages": ""},
 "datasets": {"value": "datasets used for training and evaluation", "pages": ""},
 "metrics": {"value": "main fidelity (for example FID, FVD), controllability and downstream metrics reported", "pages": ""},
 "controllability_evidence": {"value": "the experiment or result the paper uses to show control works (for example action-following error, layout consistency, perception metrics on generated data), with the key number if given", "pages": ""},
 "closed_loop": {"value": "does the paper roll the model out interactively with a driving policy (closed loop)? say yes, no or open-loop only, and for how long or how far if stated", "pages": ""},
 "stated_limitations": {"value": "limitations the paper itself states", "pages": ""},
 "notes": "anything doubtful, or empty string"
}

Strict rules:
- Use ONLY the packet text. No outside knowledge, no guessing from the paper's title or fame.
- Every "value" must be supported by the passage whose page label you put in "pages". If the packet does not support a field, set value to "not stated in packet" and pages to "". The packet is partial, so that does not mean the paper never says it.
- Keep each value under 40 words. Paraphrase; do not copy sentences. A quoted phrase must be under 10 words.
- Numbers must be copied exactly from the packet with their units.
- If the packet shows the paper is not really a driving world model or scene generator with a control input (for example a pure perception or planning model), say so in "notes" and still fill what you can.
- Do not edit any other file.

When done, reply with at most 6 lines: how many rows you wrote, and any paper whose packet was too thin or whose fields you are unsure about.
