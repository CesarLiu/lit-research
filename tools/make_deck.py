#!/usr/bin/env python3
"""Build an editable .pptx (with speaker notes) from the review and table B.

  python -I -X utf8 tools/make_deck.py runs/tableB/deck.pptx

The slide content is written out below by hand from review_A.md / table.md. Every number on a
slide must also occur in those two files: tools/check_deck.py tests that.
Style rules (from the user's earlier deck feedback): titles are assertions; body text is short
phrases, not sentences; no em dashes on slides; one visual anchor per slide; colour = control family;
whatever is written on a slide is spoken in the notes.
"""
import sys

from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

C = {  # colour carries meaning: one colour per control family, used on every slide that is about it
    "guidance": "0F766E", "trained": "4338CA", "reward": "B45309", "language": "BE123C",
    "rl": "7E22CE", "other": "64748B", "none": "A8A29E", "ink": "1F2937", "soft": "F3F4F6", "mute": "6B7280",
}
rgb = lambda h: RGBColor.from_string(h)  # noqa: E731
W, H = Inches(13.333), Inches(7.5)


def text(slide, x, y, w, h, runs, size=20, color="ink", bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """runs: str or list of paragraphs; a paragraph is a str or a list of (text, {bold,color,size}) runs."""
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    paras = runs if isinstance(runs, list) else [runs]
    for i, p in enumerate(paras):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.alignment = align
        para.space_after = Pt(4)
        for t, o in ([(p, {})] if isinstance(p, str) else p):
            r = para.add_run()
            r.text = t
            r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold)
            r.font.color.rgb = rgb(C.get(o.get("color", color), o.get("color", color)))
            r.font.name = "Calibri"
    return tb


def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE):
    s = slide.shapes.add_shape(shape, x, y, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = rgb(C.get(fill, fill))
    s.line.fill.background()
    return s


def base(prs, title, family, notes):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, Inches(0.22), H, family)
    text(s, Inches(0.6), Inches(0.35), Inches(12.2), Inches(1.1), title, size=30, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    s.notes_slide.notes_text_frame.text = notes
    return s


def blocks(s, items, family, x=Inches(0.6), y=Inches(1.7), w=Inches(7.3), h=Inches(5.3)):
    """items: [(label, [phrases])] stacked in a column."""
    paras = []
    for label, phrases in items:
        paras.append([(label.upper(), {"size": 13, "bold": True, "color": family})])
        paras += [[("   " + p, {"size": 20})] for p in phrases]
        paras.append([("", {"size": 6})])
    text(s, x, y, w, h, paras)


def anchor(s, big, caption, family, x=Inches(8.3), y=Inches(1.9), w=Inches(4.5), h=Inches(3.4)):
    rect(s, x, y, w, h, "soft", MSO_SHAPE.ROUNDED_RECTANGLE)
    rect(s, x, y, Inches(0.08), h, family)
    text(s, x + Inches(0.25), y + Inches(0.2), w - Inches(0.4), Inches(1.2), big, size=32, bold=True, color=family, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + Inches(0.25), y + Inches(1.4), w - Inches(0.4), h - Inches(1.5), caption, size=16, color="mute")


def build(out: str) -> None:
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    # 1 title ---------------------------------------------------------------
    s = prs.slides.add_slide(prs.slide_layouts[6])
    rect(s, 0, 0, W, H, "ink")
    rect(s, Inches(0.8), Inches(3.55), Inches(1.6), Inches(0.08), "guidance")
    text(s, Inches(0.8), Inches(1.7), Inches(11.5), Inches(1.8), "Controllability in driving scenario generation", size=44, bold=True, color="FFFFFF", anchor=MSO_ANCHOR.BOTTOM)
    text(s, Inches(0.8), Inches(3.8), Inches(11.5), Inches(1.4),
         ["What gets specified, and how it reaches the generator", "A review of 34 papers"], size=24, color="E5E7EB")
    s.notes_slide.notes_text_frame.text = (
        "This talk asks one question about generators of driving scenarios and traffic simulation: what does a user or designer specify, "
        "and how does that signal reach the generator. It is based on a review of thirty-four papers, built from a comparison table "
        "in which every cell points to a page. I will go through the main ways control is built in, what each one has been shown to do, "
        "where it fails, and what is still open.")

    # 2 evidence base -------------------------------------------------------
    s = base(prs, "34 papers from 636 records, each table cell tied to a page", "other",
             "The search used thirteen short keyword queries on OpenAlex and arXiv and returned six hundred thirty-six records. "
             "After removing duplicates five hundred thirty-six remained, and a keyword rule on driving and scenario terms kept three hundred seventy-one. "
             "Two hundred eighty-eight of them had an open full text. From those I chose thirty-four papers to cover different control mechanisms, "
             "and filled one table row per paper, with a page number on every cell. A separate checker audited a random sample of twenty-four cells: "
             "twenty-two supported, two partly supported and corrected, zero unsupported.")
    steps = [("636", "records found"), ("536", "after deduplication"), ("371", "on topic"), ("288", "open full text"), ("34", "in the table")]
    x0 = Inches(0.6)
    for i, (n, lab) in enumerate(steps):
        x = x0 + i * Inches(2.45)
        rect(s, x, Inches(2.0), Inches(2.25), Inches(1.9), "soft", MSO_SHAPE.ROUNDED_RECTANGLE)
        text(s, x, Inches(2.15), Inches(2.25), Inches(1.0), n, size=44, bold=True, color="guidance" if i == 4 else "ink", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        text(s, x, Inches(3.15), Inches(2.25), Inches(0.6), lab, size=16, color="mute", align=PP_ALIGN.CENTER)
    blocks(s, [("Checks", ["Page number on every cell", "Numbers tested against the source text", "24 cells audited: 22 supported, 2 partial, 0 unsupported"])],
           "other", y=Inches(4.4), w=Inches(12))

    # 3 families chart ------------------------------------------------------
    s = base(prs, "Guidance is the most common way to steer a generator", "guidance",
             "I sorted the thirty-four papers by where the control signal enters the generator. Nine are labelled inference-time guidance: eight steer a trained model with a gradient and one uses a gradient-free search. "
             "Five use language, five train conditions in, four use other routes such as adversarial search or retrieval, three tilt a reward or return, "
             "and two each fine-tune with reinforcement learning or control a latent space. Four papers have no user-steerable signal and are kept for contrast. "
             "So thirty of the thirty-four steer something, and I leave the other four out of the comparison. Colours on the following slides match these bars.")
    cd = CategoryChartData()
    cats = [("Inference-time guidance", 9, "guidance"), ("Language / LLM", 5, "language"), ("Trained-in conditions", 5, "trained"),
            ("Other (search, retrieval)", 4, "other"), ("Reward / return tilting", 3, "reward"), ("RL fine-tuning", 2, "rl"),
            ("Latent-space control", 2, "rl"), ("No control (kept for contrast)", 4, "none")]
    cd.categories = [c[0] for c in cats]
    cd.add_series("Papers", [c[1] for c in cats])
    gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(0.6), Inches(1.6), Inches(7.4), Inches(5.4), cd)
    ch = gf.chart
    ch.has_legend = False
    ch.has_title = False
    ch.plots[0].gap_width = 45
    ch.plots[0].has_data_labels = True
    ch.plots[0].data_labels.font.size = Pt(16)
    ch.plots[0].data_labels.position = XL_LABEL_POSITION.OUTSIDE_END
    ch.category_axis.reverse_order = True
    ch.category_axis.tick_labels.font.size = Pt(16)
    ch.value_axis.visible = False
    ch.value_axis.has_major_gridlines = False
    for i, c in enumerate(cats):
        pt = ch.plots[0].series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = rgb(C[c[2]])
    anchor(s, "30 of 34", "steer something; 4 have no steerable signal", "guidance", y=Inches(2.2))

    # 4 guidance ------------------------------------------------------------
    s = base(prs, "Guidance steers a trained model, at a price in realism", "guidance",
             "Problem: steer a trained generator without changing it. Idea: use an objective to steer the denoising steps, mostly through its gradient. "
             "The objective can be a collision, goal, rule or cost term. The result is a dial. In Safe-Sim, raising the time-to-collision weight from zero to two "
             "moves the collision rate from forty-eight point two to sixty point seven percent. In the pursuit-evasion paper, raising the pursuit weight from ten to sixty, "
             "together with the step size, lifts ego collisions from eighteen point nine to forty-seven point eight percent, so the weight alone cannot take the credit. "
             "The price: in Safe-Sim the realism score goes from point seven six to point eight one, and lower is better. "
             "One paper states that guidance needs differentiable, calibrated objectives, adds compute, and is sensitive to step size and weights.")
    blocks(s, [("Problem", ["Steer a trained model", "Two papers state no retraining"]),
               ("Idea", ["Objective steers each denoising step, mostly by gradient"]),
               ("How", ["Collision, goal, rule or cost terms"]),
               ("Price", ["Realism 0.76 → 0.81, lower is better", "One paper: needs differentiable, calibrated objectives", "Extra compute, sensitive to step size"])], "guidance")
    anchor(s, "48.2 → 60.7 %", "collision rate as the time-to-collision weight goes 0 → 2 (Safe-Sim)\nPursuit weight 10 → 60, step size raised too\nEgo collision 18.9 → 47.8 %", "guidance")

    # 5 trained-in ----------------------------------------------------------
    s = base(prs, "Trained-in conditions can be tested directly, within what was trained", "trained",
             "Problem: let the user set attributes directly. Idea: condition the model on the map, per-agent tokens and goals during training. "
             "Scenario Diffusion feeds agent tokens through cross-attention, and a global token controls how many agents are generated. "
             "As the token mask probability rises, the number of extra agents goes from point four to twelve point six, while the agent-token match rate stays near point nine seven. "
             "The paper varies the mask probability and infers that the global token controls density. ECoSim adds adapters to a frozen backbone and reports up to eighty-three percent lower control error, "
             "but its controls come from ground-truth trajectories and it controls a single agent. DragTraffic's evidence is mostly qualitative.")
    blocks(s, [("Problem", ["User sets agent attributes directly"]),
               ("Idea", ["Condition on map, agent tokens, goals"]),
               ("How", ["Cross-attention tokens (Scenario Diffusion)", "Adapters on a frozen backbone (ECoSim)"]),
               ("Caveats", ["ECoSim: ground-truth controls, one agent", "DragTraffic: mostly qualitative evidence"])], "trained")
    anchor(s, "0.4 → 12.6", "extra agents as token masking rises\nToken match rate stays 0.97 (Scenario Diffusion)\nControl error up to 83 % lower (ECoSim)", "trained")

    # 6 reward tilting ------------------------------------------------------
    s = base(prs, "Reward tilting gives one dial with a roughly monotone response", "reward",
             "Problem: get good or adversarial behaviour on demand. Idea: the model predicts a return distribution per agent, and one coefficient kappa tilts it. "
             "CtRL-Sim uses one coefficient per reward component, from minus twenty-five to twenty-five, and metrics change relatively monotonically. "
             "With the fine-tuned model at minus twenty-five it produces two point one times the collisions and one point eight times the off-road violations of the base model. "
             "Scenario Dreamer reuses it: the planner collision rate is four point nine percent at kappa plus ten and eleven point nine percent at minus fifty. "
             "Four limits are stated: it does not control initial placement, extreme tilting gives erratic behaviour, inference latency may make large-scale training expensive, and imitation drift can push agents off road. "
             "A later paper steers a behaviour latent over four reward channels instead, and finds map controllability depends on the reward definition.")
    blocks(s, [("Problem", ["Good or adversarial behaviour on demand"]),
               ("Idea", ["Tilt the predicted return distribution"]),
               ("How", ["One coefficient κ per reward component", "κ from −25 to +25"]),
               ("Limits", ["Initial placement not controlled", "κ = −50: erratic, implausible", "Inference latency, imitation drift", "Behaviour latent: map control depends on reward"])], "reward")
    anchor(s, "2.1× collisions", "at κ = −25, fine-tuned vs base (CtRL-Sim)\n1.8× off-road violations\nPlanner collision 4.9 % at κ = +10, 11.9 % at −50 (Scenario Dreamer)", "reward")

    # 7 language ------------------------------------------------------------
    s = base(prs, "Language control runs through LLM-written code, and some failures sit there", "language",
             "Problem: non-experts want to describe a scenario in words. Idea: an LLM turns the text into a symbolic intermediate, either a loss function or a program. "
             "In one paper GPT-4 writes a loss whose gradient guides each denoising step. In another the LLM decomposes the text, and Scenic snippets are retrieved and assembled into a program that runs in CARLA. "
             "Some stated failures sit in that intermediate. The loss-writing paper has no automatic detection or repair of a wrong loss, cannot handle commands that depend heavily on the map, "
             "and takes about a minute per scenario. A second paper's refinement struggles when the LLM's first reading is fundamentally wrong. "
             "In LD-Scene the strong adversarial level gives a collision rate of thirty-nine point three three percent, no higher than medium at forty point seven five, "
             "which the authors attribute to missed collision timing in low-speed interactions.")
    blocks(s, [("Problem", ["Describe a scenario in words"]),
               ("Idea", ["LLM turns text into a loss or a program"]),
               ("How", ["Loss gradient guides each denoising step", "Scenic snippets assembled, run in CARLA"]),
               ("Where it fails", ["No automatic detection or repair of a wrong loss", "Heavy map commands, about 1 min per scenario", "Refinement fails if first reading is wrong"])], "language")
    anchor(s, "39.33 vs 40.75 %", "collision rate at the strong and the medium adversarial level (LD-Scene)\nStronger setting, no stronger result", "language")

    # 8 narrow --------------------------------------------------------------
    s = base(prs, "Fine-tuning and latent control show narrow demonstrations", "rl",
             "Reinforcement fine-tuning of a diffusion model cuts the failure rate to point two two six under the no-collision reward and point one three six under the no-off-road reward, "
             "from point four eight three and point four five zero without it. But only those two rewards are demonstrated, so the table's notes read it as closer to constraint satisfaction. "
             "A goal-conditioned token model raises goal reach from thirty-five point three seven to fifty percent in one variant, and states the control is reasonable but imperfect. "
             "For latent control, a flow model moves the minimum time-to-collision from three point two six three to one point nine six seven and the near-miss rate from point two eight one to point five zero zero "
             "between the nominal and challenging labels. It controls the degree of criticality, not the manoeuvre. A two-page student abstract controls a discrete class only.")
    blocks(s, [("RL fine-tuning", ["Failure rate 0.226 / 0.136 vs 0.483 / 0.450 without", "Only collision and off-road rewards", "Goal reach 35.37 → 50.00 %"]),
               ("Latent control", ["Time-to-collision measure (minSTTC) 3.263 → 1.967", "Near-miss rate 0.281 → 0.500", "Degree of criticality, not the manoeuvre", "Student abstract: discrete class only"])], "rl")
    anchor(s, "2 rewards", "the only objectives shown in one fine-tuning paper\nCollision and off-road", "rl")

    # 9 cross-cutting -------------------------------------------------------
    s = base(prs, "Three patterns cut across the families", "other",
             "First, safety-critical generation is a frequent steered quantity: at least eleven of the thirty papers with any control steer collisions or adversarial strength. "
             "That partly reflects how I chose the papers from abstracts, so it describes this sample, not the field. "
             "Second, demonstrated control is often narrow: collision and off-road, goals, a discrete class, behaviour but not placement, and one agent in ECoSim. "
             "Some rows show wider signals, four reward channels and six temporal-logic rules. "
             "Third, results are hard to compare across papers: they report collision rate, goal reach, token match rate, control error or human preference, mostly on different data and baselines, with a few shared setups. "
             "So I make no ranking.")
    blocks(s, [("1  Adversarial focus", ["Collisions or adversarial strength is often what gets steered"]),
               ("2  Often narrow", ["A class, goals, collisions, one agent", "Wider: four reward channels, six rules"]),
               ("3  Hard to compare", ["Mostly different metrics, data and baselines", "So no ranking"])], "other")
    anchor(s, "11 of 30", "papers with control steer collisions or adversarial strength\n(partly my selection from abstracts)", "other")

    # 10 gaps ---------------------------------------------------------------
    s = base(prs, "Open problems the evidence supports", "other",
             "The rows support five open points. No row shows a shared controllability benchmark: metrics and data differ, though two language papers both evaluate on SafeBench. "
             "Several models cover vehicles only: two papers say only vehicles are modelled, and a third says only its adversarial agents are vehicles. Control of more than one agent is a stated weakness in ECoSim, "
             "which controls a single agent and may favour control satisfaction over safe interaction when instructions conflict with traffic. "
             "For the language papers that go through code or a loss, reliability depends on what the LLM writes. And for reward tilting, the open items are placement control, extreme tilt, "
             "inference latency and imitation drift, and for the behaviour-latent paper, map controllability that depends on the reward definition.")
    blocks(s, [("Evaluation", ["No shared controllability benchmark"]),
               ("Scope", ["Vehicles only in several models", "One controlled agent (ECoSim)"]),
               ("Language", ["Reliability set by what the LLM writes"]),
               ("Reward tilting", ["Placement control, extreme tilt", "Latency, imitation drift", "Map control tied to reward definition"])], "other", w=Inches(12))

    # 11 validity -----------------------------------------------------------
    s = base(prs, "The table is spot-checked; the full texts are not yet read by a person", "other",
             "A caveat on trust. Each row came from the first two pages plus the best passages of the paper, not the whole paper, so not stated in packet does not mean the paper omits it. "
             "Rows were filled by Claude sub-agents. Automated checks confirmed the format, the pages, and that numbers occur in the source text, though that test is weak for short numbers. "
             "An independent audit of twenty-four cells found twenty-two supported, two partly supported and both corrected, and zero unsupported; the other fields were not audited. "
             "A second model then checked every sentence of the review against the table rows it cites. The first pass found nineteen sentences only partly supported and one unsupported, "
             "so I revised the text and checked again until none was unsupported. That shows the review follows the table, not that the table is right. "
             "I chose the papers from abstracts, the family labels are judgement calls, and only open-access papers are included. No person has read the PDFs.")
    blocks(s, [("Done", ["Page on every cell, numbers tested against text", "24-cell audit: 22 / 2 / 0 (supported / partial / unsupported)", "Every review sentence checked against its rows"]),
               ("Not done", ["No person has read the full PDFs", "Data, metrics and limits fields not audited"]),
               ("Bias", ["Papers chosen from abstracts", "Open access only", "Family labels are judgement calls"])], "other", w=Inches(12))

    # 12 takeaways ----------------------------------------------------------
    s = base(prs, "Four mechanisms, four different failure points", "guidance",
             "To close, one line per mechanism. Guidance steers a trained model and costs realism. Trained-in conditions steer attributes, map and goals, which can be tested directly but with uneven evidence, and ECoSim controls a single agent. "
             "Reward tilting is one dial with a roughly monotone response, with stated limits on placement and extreme values. For language papers that use code or a loss, reliability depends on what the model writes. "
             "The open question that cuts across all of them is a shared way to measure controllability.")
    rows = [("Guidance", "guidance", "Differentiable objectives", "Realism cost, compute"),
            ("Trained-in conditions", "trained", "Attributes, map, goals", "Uneven evidence, one agent"),
            ("Reward tilting", "reward", "One dial, roughly monotone", "Placement, extreme tilt"),
            ("Language", "language", "Descriptions in words", "What the LLM writes")]
    text(s, Inches(0.6), Inches(1.7), Inches(3.4), Inches(0.5), "MECHANISM", size=13, bold=True, color="mute")
    text(s, Inches(4.3), Inches(1.7), Inches(4.2), Inches(0.5), "STEERS", size=13, bold=True, color="mute")
    text(s, Inches(8.8), Inches(1.7), Inches(4.2), Inches(0.5), "FAILS WHERE", size=13, bold=True, color="mute")
    for i, (a, fam, b, c) in enumerate(rows):
        y = Inches(2.25) + i * Inches(1.15)
        rect(s, Inches(0.6), y, Inches(12.2), Inches(0.95), "soft", MSO_SHAPE.ROUNDED_RECTANGLE)
        rect(s, Inches(0.6), y, Inches(0.1), Inches(0.95), fam)
        text(s, Inches(0.9), y, Inches(3.3), Inches(0.95), a, size=22, bold=True, color=fam, anchor=MSO_ANCHOR.MIDDLE)
        text(s, Inches(4.3), y, Inches(4.3), Inches(0.95), b, size=20, anchor=MSO_ANCHOR.MIDDLE)
        text(s, Inches(8.8), y, Inches(3.9), Inches(0.95), c, size=20, anchor=MSO_ANCHOR.MIDDLE)

    prs.save(out)
    print(f"saved {out}: {len(prs.slides)} slides")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "deck.pptx")
