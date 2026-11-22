You are extracting atomic, checkable claims from the evidence packet of one paper on controllable driving-scenario or traffic-simulation generation. Someone will later try to reproduce each claim by running the paper's code, so each claim must be one number under one stated condition.

Input: the list of paper ids in {GROUP_FILE} (one id per line). For each id, read the evidence packet {RUN_DIR}\packets\<id>.md. A packet holds the paper's first two pages plus the best passages from the paper for five topics. Passages are labelled [pages X-Y].

Output: for each id, write {RUN_DIR}\atomic\<id>.json containing exactly this JSON object (valid JSON, UTF-8):
{
 "id": "<id>",
 "claims": [
  {
   "claim": "one sentence: what is measured, under which condition, and the value",
   "kind": "control_effect" | "main_result" | "ablation",
   "metric": "the metric name as the paper uses it",
   "condition": "the setting, dataset, model variant or control setting under which the value was measured",
   "reported_value": "the single number with its unit, copied exactly from the packet",
   "comparison": "the baseline or other setting this value is compared with, or an empty string",
   "quote": "a verbatim passage from the packet that contains the value, at most 30 words",
   "page": "the page label of the passage, for example 6-7"
  }
 ]
}

Strict rules:
- Use ONLY the packet text. No outside knowledge.
- One number per claim. A before and after pair (for example a collision rate that goes from 48.2 to 60.7) is two claims, each with its own condition.
- Prefer claims that show the control works (kind control_effect: a value that changes as the control setting changes). Then the main reported result (main_result), then ablations. At most 6 claims per paper; fewer is fine.
- The quote must be copied character for character from the packet, including its odd line breaks or symbols, and must contain the number. Do not paraphrase it.
- Numbers are copied exactly with their units. Do not compute, round or convert anything. If the packet shows a table so flattened that you cannot tell which number belongs to which row or column, skip that number.
- The condition must be specific enough that someone could set it up: name the control setting, the baseline and the dataset if the packet gives them. If the packet does not give them, say "not stated in packet" in that field.
- If the paper reports no checkable numbers in the packet, write an empty claims list.
- Do not edit any other file.

When done, reply with at most 5 lines: how many claims you wrote per paper, and any paper whose packet was too thin or whose table was too flattened to use.
