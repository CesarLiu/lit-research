"""Pieces of paper-qa (FutureHouse, Apache-2.0) ported as dependency-free code.

Source: https://github.com/Future-House/paper-qa (src/paperqa/{prompts,core,utils,readers,llms,settings}.py)
Changes: removed pydantic / litellm / tiktoken / aviary / numpy; chunking works on a
{page: text} dict; MMR works on sparse vectors; added a small TF-IDF vectoriser as a
stand-in for paper-qa's embedding model. See ../../NOTICE-paper-qa.md.

Contents
  prompts        summary / QA prompts, verbatim from paper-qa
  defaults       evidence_k etc. from paper-qa's Settings
  extract_score, strip_citations, llm_parse_json   LLM-reply cleaning
  strings_similarity                               word-set Jaccard
  chunk_pages                                      page-aware chunking
  TfidfIndex, mmr_select                           retrieval (no embeddings, no key)
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter

# ----------------------------------------------------------------- prompts (prompts.py)

CANNOT_ANSWER_PHRASE = "I cannot answer"

SUMMARY_JSON_SYSTEM_PROMPT = (
    "Provide a summary of the relevant information"
    " that could help answer the question based on the excerpt."
    " Your summary, combined with many others,"
    " will be given to the model to generate an answer."
    " Respond with the following JSON format:"
    '\n\n{{\n  "summary": "...",\n  "relevance_score": 0-10\n}}'
    "\n\nwhere `summary` is relevant information from the text - {summary_length}."
    " `relevance_score` is an integer 0-10 for the relevance of `summary` to the question."
    "\n\nThe excerpt may or may not contain relevant information."
    " If not, leave `summary` empty, and make `relevance_score` be 0."
)
SUMMARY_JSON_USER_PROMPT = "Excerpt from {citation}\n\n---\n\n{text}\n\n---\n\nQuestion: {question}"

CITATION_KEY_CONSTRAINTS = (
    "## Valid citation examples, only use comma/space delimited parentheticals:\n"
    "- (pqac-d79ef6fa, pqac-0f650d59)\n"
    "- (pqac-d79ef6fa)\n"
    "## Invalid citation examples:\n"
    "- (pqac-d79ef6fa and pqac-0f650d59)\n"
    "- (pqac-d79ef6fa;pqac-0f650d59)\n"
    "- (pqac-d79ef6fa-pqac-0f650d59)\n"
    "- pqac-d79ef6fa and pqac-0f650d59\n"
    "- Example's work (pqac-d79ef6fa)\n"
    "- (pages pqac-d79ef6fa)\n"
    "- Author et al. (2023)"
)
QA_PROMPT = (
    "Answer the question below with the context.\n\n"
    "Context:\n\n{context}\n\n---\n\n"
    "Question: {question}\n\n"
    "Write an answer based on the context. "
    "If the context provides insufficient information reply "
    f'"{CANNOT_ANSWER_PHRASE}." '
    "For each part of your answer, indicate which sources most support "
    "it via citation keys at the end of sentences, like {example_citation}. "
    "Only cite from the context above and only use the citation keys from the context."
    f"\n\n{CITATION_KEY_CONSTRAINTS}\n\n"
    "Do not concatenate citation keys, just use them as is. "
    "Write in the style of a scientific article, with concise sentences and "
    "coherent paragraphs. This answer will be used directly, "
    "so do not add any extraneous information.\n\n"
    "Answer ({answer_length}):"
)
CONTEXT_OUTER_PROMPT = "{context_str}\n\nValid Keys: {valid_keys}"
CONTEXT_INNER_PROMPT = "{name}: {text}\nFrom {citation}"

# ----------------------------------------------------------------- defaults (settings.py)

EVIDENCE_K = 10  # chunks sent to summarization
EVIDENCE_SUMMARY_LENGTH = "about 100 words"
EVIDENCE_RELEVANCE_SCORE_CUTOFF = 1
ANSWER_MAX_SOURCES = 5
ANSWER_LENGTH = "about 200 words, but can be longer"
CHUNK_CHARS = 5000
CHUNK_OVERLAP = 250

# ----------------------------------------------------------------- reply cleaning (utils.py, core.py)


def strip_citations(text: str) -> str:
    """Drop in-text citations from a summary so they cannot collide with our own keys."""
    regex = r"\b[\w\-]+\set\sal\.\s\([0-9]{4}\)|\((?:[^\)]*?[a-zA-Z][^\)]*?[0-9]{4}[^\)]*?)\)"
    return re.sub(regex, "", text, flags=re.MULTILINE)


def extract_score(text: str) -> int:
    """Score 1-10 from free text; 0 is the 'not applicable' sentinel."""
    last_line = text.rsplit("\n", maxsplit=1)[-1]
    if "n/a" in last_line.lower() or "not applicable" in text.lower() or "not relevant" in text.lower():
        return 0
    score = re.search(r"[sS]core[:is\s]+([0-9]+)", text)
    if not score:
        score = re.search(r"\(([0-9])\w*\/", text)
    if not score:
        score = re.search(r"([0-9]+)\w*\/", text)
    if score:
        s = int(score.group(1))
        return int(s / 10) if s > 10 else s
    scores = re.findall(r"([0-9]+)", text[-15:])
    if scores:
        s = int(scores[-1])
        return int(s / 10) if s > 10 else s
    raise ValueError(f"Failed to extract score from text {text!r}.")


def llm_parse_json(text: str) -> dict:
    """Tolerant parser for the {"summary", "relevance_score"} reply."""
    ptext = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    ptext = ptext.split("```json")[-1].split("```")[0]
    ptext = re.sub(
        r'"relevance_score"\s*:\s*(\d+)/(\d+)',
        lambda m: f'"relevance_score": {round(int(m.group(1)) / int(m.group(2)) * 10)}',
        ptext,
    )
    if "{" not in ptext and "}" not in ptext:
        ptext = json.dumps({"summary": ptext})
    ptext = ("{" + ptext.split("{", 1)[-1]).rsplit("}", 1)[0] + "}"
    ptext = re.sub(r'"(?:[^"\\]|\\.)*"', lambda m: m.group(0).replace("\n", "\\n"), ptext)
    ptext = re.sub(r'\\([^"\\/bfnrtu])', r"\\\\\1", ptext)

    def fraction_replacer(m: re.Match) -> str:
        if m.group(2) and m.group(3):
            num, den = int(m.group(2)), int(m.group(3))
        elif m.group(4) and m.group(5):
            num, den = int(m.group(4)), int(m.group(5))
        else:
            return m.group(0)
        return f"{m.group(1)}{round(num / den * 10)}"

    ptext = re.sub(
        r'("\s*(?:relevance|score)[\w\s\-]*"\s*:\s*)(?:"(\d+)\s*/\s*(\d+)"|(\d+)\s*/\s*(\d+))',
        fraction_replacer,
        ptext,
    )
    ptext = re.sub(r'(?<=[}\]0-9"])\s*(?="[^"\\]*"\s*:)', ", ", ptext)
    ptext = re.sub(r",\s*,+", ",", ptext)
    ptext = re.sub(r",\s*}", "}", ptext)
    ptext = re.sub(r"\{\s*,", "{", ptext)
    try:
        data = json.loads(ptext)
    except json.JSONDecodeError as e:
        if "summary" in ptext and '"relevance_score"' in ptext:
            s = re.search(r'"summary"\s*:\s*"(.*?)",\s*"relevance_score"', ptext, re.DOTALL)
            sc = re.search(r'"relevance_score"\s*:\s*"?(\d+)"?', ptext)
            if s and sc:
                return {"summary": s.group(1).replace(r"\'", "'"), "relevance_score": int(sc.group(1))}
        raise ValueError(f"Failed to load JSON from text {text!r}.") from e
    for key in list(data):
        if re.search(r"relevance|score", key, re.IGNORECASE):
            data["relevance_score"] = data.pop(key)
    if "relevance_score" in data and not isinstance(data["relevance_score"], int):
        data["relevance_score"] = round(float(data["relevance_score"]))
    return data


def strings_similarity(s1: str, s2: str, case_insensitive: bool = True) -> float:
    """Word-set Jaccard, as paper-qa uses for its 0.75 title threshold."""
    if not s1 or not s2:
        return 0.0
    a = set(s1.lower().split()) if case_insensitive else set(s1.split())
    b = set(s2.lower().split()) if case_insensitive else set(s2.split())
    return len(a & b) / len(a | b)


# ----------------------------------------------------------------- chunking (readers.chunk_pdf)


def chunk_pages(pages: dict[str, str], chunk_chars: int = CHUNK_CHARS, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Same algorithm as paper-qa's chunk_pdf. Returns [{text, pages: 'lo-hi'}]."""
    out: list[dict] = []
    split, seen = "", []

    def make(txt: str, lo: str, hi: str) -> dict:
        return {"text": txt, "pages": lo if lo == hi else f"{lo}-{hi}"}

    for page_num, page_text in pages.items():
        split += page_text
        seen.append(page_num)
        while len(split) > chunk_chars:
            out.append(make(split[:chunk_chars], seen[0], seen[-1]))
            split = split[chunk_chars - overlap :]
            seen = [page_num]
    if len(split) > overlap or not out:
        out.append(make(split[:chunk_chars], seen[0], seen[-1]))
    return out


# ----------------------------------------------------------------- retrieval (llms.py MMR)

_STOP = set(
    "a an the of and or in on for to with by is are was were be been this that these those it its as at from "
    "we our their can may also than which not but if into using used use based via".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if len(t) > 1 and t not in _STOP]


def _cos(a: dict, b: dict) -> float:
    if len(a) > len(b):
        a, b = b, a
    dot = sum(w * b.get(t, 0.0) for t, w in a.items())
    na = math.sqrt(sum(w * w for w in a.values()))
    nb = math.sqrt(sum(w * w for w in b.values()))
    return dot / (na * nb) if na and nb else 0.0


class TfidfIndex:
    """Sparse TF-IDF over chunks. Stand-in for paper-qa's embedding model (NOT from paper-qa)."""

    def __init__(self, texts: list[str]):
        docs = [Counter(_tokens(t)) for t in texts]
        df = Counter(t for d in docs for t in d)
        n = len(docs)
        self.idf = {t: math.log((1 + n) / (1 + c)) + 1.0 for t, c in df.items()}
        self.vecs = [self._weigh(d) for d in docs]

    def _weigh(self, counts: Counter) -> dict:
        return {t: (1 + math.log(c)) * self.idf[t] for t, c in counts.items() if t in self.idf}

    def search(self, query: str, fetch_k: int) -> list[tuple[int, float]]:
        q = self._weigh(Counter(_tokens(query)))
        scored = [(i, _cos(q, v)) for i, v in enumerate(self.vecs)]
        scored = [x for x in scored if x[1] > 0]
        return sorted(scored, key=lambda x: -x[1])[:fetch_k]


def mmr_select(index: TfidfIndex, candidates: list[tuple[int, float]], k: int, mmr_lambda: float = 0.9) -> list[int]:
    """Maximal Marginal Relevance, same recurrence as paper-qa's VectorStore.

    candidates are (chunk_id, score) sorted by score. lambda >= 1 disables diversity (paper-qa's
    own default for the text index, texts_index_mmr_lambda, is 1.0, i.e. off).
    """
    if len(candidates) <= k or mmr_lambda >= 1.0:
        return [i for i, _ in candidates[:k]]
    ids = [i for i, _ in candidates]
    scores = [s for _, s in candidates]
    sim = [[_cos(index.vecs[a], index.vecs[b]) for b in ids] for a in ids]
    chosen = [0]
    while len(chosen) < k:
        best, best_val = None, -math.inf
        for j in range(len(ids)):
            if j in chosen:
                continue
            val = mmr_lambda * scores[j] - (1 - mmr_lambda) * max(sim[j][c] for c in chosen)
            if val > best_val:
                best, best_val = j, val
        chosen.append(best)
    return [ids[j] for j in chosen]
