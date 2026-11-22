You are filling one row of a comparison table per paper, about HOW CONTROLLABILITY IS ACHIEVED in driving scenario / traffic simulation generation models.

Input: the list of paper ids in {GROUP_FILE} (one id per line). For each id, read the evidence packet {RUN_DIR}\packets\<id>.md. A packet holds the paper's first two pages plus the best passages from the paper for five topics. Passages are labelled [pages X-Y].

Output: for each id, write {RUN_DIR}\rows\<id>.json containing exactly this JSON object (valid JSON, UTF-8):
{
 "id": "<id>",
 "title": "<paper title from the packet>",
 "control_family": one of "reward/return conditioning" | "inference-time guidance" | "conditioning inputs (trained in)" | "language/LLM-driven" | "latent-space control" | "RL fine-tuning" | "none/uncontrolled" | "other" | "not stated in packet",
 "control_signal":  {"value": "what a user or designer specifies to steer generation", "pages": "e.g. 3-4"},
 "control_mechanism": {"value": "how that signal is injected (e.g. cross-attention, guidance loss during sampling, reward tilting, latent code, LLM prompt, fine-tuning)", "pages": ""},
 "base_model": {"value": "model family and key components", "pages": ""},
 "datasets": {"value": "datasets used for training/evaluation", "pages": ""},
 "metrics": {"value": "main realism and controllability/safety metrics reported", "pages": ""},
 "controllability_evidence": {"value": "the experiment or result the paper uses to show control works, with the key number if given", "pages": ""},
 "stated_limitations": {"value": "limitations the paper itself states", "pages": ""},
 "notes": "anything doubtful, or empty string"
}

Strict rules:
- Use ONLY the packet text. No outside knowledge, no guessing from the paper's title or fame.
- Every "value" must be supported by the passage whose page label you put in "pages". If the packet does not support a field, set value to "not stated in packet" and pages to "". The packet is partial, so that does not mean the paper never says it.
- Keep each value under 40 words. Paraphrase; do not copy sentences. A quoted phrase must be under 10 words.
- Numbers must be copied exactly from the packet with their units.
- If the packet shows the paper is not really about controllable generation (for example a survey or a pure prediction model), say so in "notes" and still fill what you can.
- Do not edit any other file.

When done, reply with at most 6 lines: how many rows you wrote, and any paper whose packet was too thin or whose fields you are unsure about.
