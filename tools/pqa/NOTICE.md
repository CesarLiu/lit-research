# Notice

`pqa_port.py` contains code and prompt text adapted from paper-qa
(https://github.com/Future-House/paper-qa, Apache License 2.0, copyright FutureHouse Inc.).
Full licence text: `LICENSE-paper-qa`.

Taken from paper-qa (modified: pydantic/litellm/tiktoken/numpy removed, async removed):
- prompts.py: summary JSON system/user prompts, QA prompt, citation key constraints, context prompts
- core.py: `llm_parse_json`
- utils.py: `extract_score`, `strip_citations`, `strings_similarity`
- readers.py: `chunk_pdf` algorithm (page-aware chunking)
- llms.py: MMR selection recurrence
- settings.py: default values (evidence_k, chunk size/overlap, answer_max_sources, ...)

Not from paper-qa: the TF-IDF index, `rcs.py`, `make_manifest.py`, and the ID/title agreement check in
`../verify_citations_arxiv.py` (inspired by paper-qa's title-and-author metadata queries).
