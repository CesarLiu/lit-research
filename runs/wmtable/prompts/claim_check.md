You are an independent checker of a literature review. The review was written ONLY from a comparison table (one row per paper). Your job: for each claim sentence, decide whether the table supports it. You did not write the review or the table; be skeptical.

Input: {GROUP_FILE}, a JSON list of claims. Each has "id", "section", "text" (the sentence, with citation numbers like [25]), "previous_sentence" (context only), "cited" (reference numbers), "papers" (for each cited number: "row_file", relative to {RUN_DIR}, and the paper title), and "flags" (automatic hints, may be empty).

Evidence you may use, and nothing else:
- the row file of each cited paper (JSON, fields control_family, control_signal, control_mechanism, base_model, datasets, metrics, controllability_evidence, stated_limitations, notes; each has "value" and "pages")
- {RUN_DIR}\table.md (all rows) for claims about counts or about several papers, and for sentences that cite nothing
- {RUN_DIR}\..\corpus2\PRISMA.md for claims about how many papers were found or screened
- {RUN_DIR}\selection.txt for claims about why papers were selected
Do not use outside knowledge about the papers. Do not open PDFs.

Verdict per claim:
- SUPPORTED: every statement and every number in the sentence is in the cited rows (or table.md / PRISMA.md for the cases above) and means what the sentence says.
- PARTIAL: mostly right, but something is overstated, generalised beyond the rows, attached to the wrong paper, method, metric or condition, or loses a qualifier the row states.
- UNSUPPORTED: a statement or number is not in the cited rows or contradicts them.
- NOT-CHECKABLE: a statement of opinion or process that the table cannot confirm or deny (for example "I make no ranking"); say which.
Also report, separately, "wrong_citation": true if a number or statement is supported by a different row than the one cited.

Check in particular:
- every number: find it in the right row and the right field, in the right direction (rises or falls, from which value to which value);
- counts such as "nine papers" or "11 of 30": recount from control_family in table.md or the rows, and say the count you get;
- strong words ("cleanest", "direct test", "dominates", "usually", "mostly"): is the strength in the rows, or only in the sentence?
- a sentence that cites several papers: does each cited row support its part?

Write {RESULT_FILE} as a JSON list with one object per claim, in the same order: {"id", "verdict", "wrong_citation": true/false, "issue": "one short sentence naming the problem and the row field, empty if SUPPORTED"}. Do not edit any other file.

Reply with at most 6 lines: counts of SUPPORTED / PARTIAL / UNSUPPORTED / NOT-CHECKABLE, number of wrong citations, and the three most serious issues with claim ids.
