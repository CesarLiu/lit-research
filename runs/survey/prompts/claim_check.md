You are an independent checker of a survey report. The report was written ONLY from three evidence sets: two comparison tables (one row per paper) and a set of company statements with verbatim quotes. Your job: for each claim sentence, decide whether that evidence supports it. You did not write the report; be skeptical.

Input: {GROUP_FILE}, a JSON list of claims. Each has "id", "section", "text" (the sentence; [n] is a paper, [W1]-style codes are company statements), "previous_sentence" (context only), "cited" (paper numbers), "papers" (for each: "row_file", relative to {RUN_DIR}, and the title), "company_statements" (for each cited company code: company, date, claim, verbatim quote, grade, page file), and "flags" (automatic hints).

Evidence you may use, and nothing else:
- the row file of each cited paper (JSON; scenario-table rows have control_signal, control_mechanism, base_model, datasets, metrics, controllability_evidence, stated_limitations, notes; world-model rows have output_modality, control_signal, control_mechanism, base_model, datasets, metrics, controllability_evidence, closed_loop, stated_limitations, notes; each field has "value" and "pages")
- the company statements attached to the claim
- {RUN_DIR}\..\tableC\table.md and {RUN_DIR}\..\wmtable\table.md (all rows of the two tables) for claims about counts, families or several papers, and for sentences that cite nothing; rows of both tables are also in {RUN_DIR}\rows
- for claims about how the evidence was gathered (numbers of papers, searches, screening, audits): {RUN_DIR}\..\wm\wm_screening.csv, {RUN_DIR}\..\wm\screening_log.csv, {RUN_DIR}\..\wm\known_papers.txt, {RUN_DIR}\..\chain\chain_screening.csv, {RUN_DIR}\..\chain2\fulltext\oa_report.json, {RUN_DIR}\..\corpus2\PRISMA.md, {RUN_DIR}\..\tableC\audit_result.json, {RUN_DIR}\..\wmtable\audit_result.json, {RUN_DIR}\..\tableB\audit_result.json, {RUN_DIR}\..\industry\industry_scan.md
Do not use outside knowledge about the papers or companies. Do not open PDFs.

Verdict per claim:
- SUPPORTED: every statement and every number in the sentence is in the cited rows or company statements (or the files listed for process claims) and means what the sentence says.
- PARTIAL: mostly right, but something is overstated, generalised beyond the rows, attached to the wrong paper, method, metric or condition, or loses a qualifier the row states.
- UNSUPPORTED: a statement or number is not in the cited evidence or contradicts it.
- NOT-CHECKABLE: a proposal, an opinion, or a statement about the report itself that the evidence cannot confirm or deny (for example a research direction in section 7, or "I make no ranking"); say which. For a section 7 item, check its "Gap:" statement against the evidence and give the verdict for that part; mark only the proposal itself NOT-CHECKABLE.
Also report, separately, "wrong_citation": true if a number or statement is supported by a different cited item than the one it is attached to, or by an item that is not cited.

Check in particular:
- every number: find it in the right row and the right field, in the right direction (rises or falls, from which value to which value);
- counts such as "16 of the 64 papers": recount from the table files (control_family, closed_loop and so on) and say the count you get;
- company claims: the sentence must not say more than the quote and its grade allow (marketing wording is not a result);
- strong words ("most", "mostly", "usually", "clearly", "dominates"): is the strength in the evidence or only in the sentence?
- a sentence that cites several items: does each cited item support its part?

Write {RESULT_FILE} as a JSON list with one object per claim, in the same order: {"id", "verdict", "wrong_citation": true/false, "issue": "one short sentence naming the problem and the row field or file, empty if SUPPORTED"}. Do not edit any other file.

Reply with at most 6 lines: counts of SUPPORTED / PARTIAL / UNSUPPORTED / NOT-CHECKABLE, number of wrong citations, and the three most serious issues with claim ids.
