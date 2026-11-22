You are an independent auditor. A table about controllable driving-scenario generation was filled from per-paper evidence packets. Check a sample of its cells against the packets.

Input: {RUN_DIR}\audit_cells.json, a list of {N_CELLS} cells. Each has "packet" (path relative to {RUN_DIR}), "field", "claimed_value", "claimed_pages".

For each cell, read the packet and judge ONLY from the packet text whether claimed_value is supported. Verdicts:
- SUPPORTED: every factual statement and every number in the claim is in the packet and says what the claim says.
- PARTIAL: mostly right, but something is overstated, mixed up (for example a number attached to the wrong method, metric, or column), or missing a qualifier the packet states.
- UNSUPPORTED: a statement or number is not in the packet or contradicts it.
Also check that the cited pages match the [pages ...] label of the passage containing the evidence; report PAGE-MISMATCH if not (this is separate from the verdict).

Be skeptical: for numbers in tables, locate the row and column; do not accept a number just because it appears somewhere. Do not use outside knowledge about the papers. Do not edit any file except the output below.

Write {RUN_DIR}\audit_result.json as a JSON list with one object per cell: {"packet","field","verdict","page_mismatch": true/false,"issue": "one short sentence, empty if SUPPORTED and pages OK"}.

Reply with at most 5 lines: counts of SUPPORTED / PARTIAL / UNSUPPORTED, counts of page mismatches, and the two most serious issues.
