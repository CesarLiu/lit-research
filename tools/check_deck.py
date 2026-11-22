#!/usr/bin/env python3
"""Check a deck built by make_deck.py.

  python -I -X utf8 tools/check_deck.py DECK.pptx SOURCE1.md [SOURCE2.md ...]

1. no em dash on a slide
2. every number on a slide occurs in a source file
3. every number on a slide is spoken in that slide's notes (digits read as words)
4. notes length per slide and in total, at 105 words per minute
5. rough text-overflow estimate for every text box (character-width heuristic, not a render)
"""
import math
import re
import sys

from pptx import Presentation
from pptx.util import Emu

ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()
NUM = re.compile(r"\d+(?:\.\d+)?")


def words(n: int) -> str:
    if n < 20:
        return ONES[n]
    if n < 100:
        return TENS[n // 10] + ("" if n % 10 == 0 else "-" + ONES[n % 10])
    if n < 1000:
        return ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + words(n % 100))
    return str(n)


def spoken(tok: str) -> set[str]:
    """Acceptable spoken forms of a number token, normalised (lower case, hyphen -> space)."""
    whole, _, frac = tok.partition(".")
    base = words(int(whole))
    if not frac:
        return {base.replace("-", " ")}
    f = " ".join(ONES[int(d)] for d in frac)
    forms = {f"{base} point {f}"}
    if whole == "0":
        forms.add(f"point {f}")
    if set(frac) == {"0"}:  # 50.00 may be said "fifty"
        forms.add(base)
    return {x.replace("-", " ") for x in forms}


def shape_text(sh) -> str:
    out = []
    if sh.has_text_frame:
        out.append(sh.text_frame.text)
    if getattr(sh, "has_chart", False) and sh.has_chart:
        out += [str(c) for c in sh.chart.plots[0].categories]
    return "\n".join(out)


def main(deck: str, sources: list[str]) -> int:
    src = " ".join(open(p, encoding="utf-8").read() for p in sources)
    src_nums = set(NUM.findall(src))
    prs = Presentation(deck)
    problems, total_words = [], 0
    for i, sl in enumerate(prs.slides, 1):
        txt = "\n".join(shape_text(sh) for sh in sl.shapes)
        notes = sl.notes_slide.notes_text_frame.text if sl.has_notes_slide else ""
        nn = re.sub(r"\s+", " ", notes.lower().replace("-", " "))
        if "—" in txt:
            problems.append(f"slide {i}: em dash on slide")
        for tok in sorted(set(NUM.findall(txt))):
            if tok not in src_nums and not (tok.rstrip("0").rstrip(".") in src_nums):
                problems.append(f"slide {i}: number {tok} not in sources")
            if not any(f in nn for f in spoken(tok)) and not (len(tok) == 1 and tok in "123"):
                problems.append(f"slide {i}: number {tok} not spoken in notes (expected e.g. '{sorted(spoken(tok))[0]}')")
        n = len(notes.split())
        total_words += n
        print(f"slide {i:2d}: notes {n:3d} words, about {n / 105:.1f} min")
        for sh in sl.shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            wid = Emu(sh.width).inches - 0.1
            need = 0.0
            for p in sh.text_frame.paragraphs:
                sz = max((r.font.size.pt for r in p.runs if r.font.size), default=18)
                chars = sum(len(r.text) for r in p.runs)
                lines = max(1, math.ceil(chars * 0.5 * sz / 72 / wid))
                need += lines * sz * 1.2 / 72 + 4 / 72
            if need > Emu(sh.height).inches * 1.02:
                problems.append(f"slide {i}: text box may overflow ({need:.1f} in needed, {Emu(sh.height).inches:.1f} in high): {sh.text_frame.text[:40]!r}")
    print(f"total notes {total_words} words, about {total_words / 105:.1f} min at 105 words/min")
    print("\n".join(problems) if problems else "no problems found")
    return 1 if problems else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    raise SystemExit(main(a[0], a[1:]) if len(a) >= 2 else print(__doc__) or 2)
