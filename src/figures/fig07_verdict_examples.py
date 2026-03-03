"""fig07_verdict_examples.py — Pipeline output: AI harmonization verdict examples.

Table of 5 real CPS--ACS question pairs spanning all feasibility tiers.
Columns: source question, ACS question, tier, barrier, confidence, and AI
rater reasoning. Wide (16:9) format for slide presentation.

Pair IDs (from pipeline output):
  CPS_0858 (F1 disability), CPS_0962 (F1 earnings), CPS_0212 (F2 veterans),
  CPS_0040 (F3 hours), CPS_0186 (F3 unemployment)

Sources: cps_comparison_merged.csv joined to final_verdicts.csv.
Reasoning text is from Stage 2 claude-haiku-4-5 rater (prose per pair).

Outputs: report/figures/fig07_verdict_examples.pdf + .png
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
from topic_colors import FIGURE_DPI

# ---------------------------------------------------------------------------
# Data
# Question texts cleaned/wrapped for display; full texts in handoffs/
# ---------------------------------------------------------------------------
HEADER = ["Source Question (CPS)", "ACS Question", "Tier", "Barrier", "Conf.", "AI Rater Reasoning"]

ROWS = [
    [
        "(Do/Does name) have difficulty\ndressing or bathing?",
        "Does this person have difficulty\ndressing or bathing?",
        "F1",
        "NHB.0",
        "HIGH",
        "Same self-care concept. CPS adapts\nphrasing for household context only.",
    ],
    [
        "(Name's/your) hourly rate of pay\non this job, excl. overtime/tips?",
        "Excl. overtime/tips, what is your\nhourly rate of pay on this job?",
        "F1",
        "NHB.0",
        "HIGH",
        "Identical exclusions and job framing;\nstylistic word-order difference only.",
    ],
    [
        "Did (name/you) ever serve on\nactive duty in U.S. Armed Forces?",
        "Has this person ever served on active\nduty in Armed Forces, Reserves, or Guard?",
        "F2",
        "CC.4",
        "HIGH",
        "ACS explicitly adds Reserves/Guard;\nCPS yes-respondents are a subset.",
    ],
    [
        "Exact number of hours (name/you)\nworked last week (actual, not usual)?",
        "How many hours do you usually\nwork per week at this rate?",
        "F3",
        "CC.2",
        "HIGH",
        "Actual hours in specific week vs. usual;\ngap is non-trivial in volatile employment.",
    ],
    [
        "(Has name/you) been doing anything\nto find work in the last 4 weeks?",
        "Has this person been told they will\nbe recalled within the next 6 months?",
        "F3",
        "CC.1",
        "HIGH",
        "CPS = active job search (past 4 wks);\nACS = employer recall notice (future).",
    ],
]

# Tier color key per row — two F3 rows get distinct colors
ROW_TIER_KEYS = ["F1", "F1", "F2", "F3a", "F3f"]

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY       = "#112E51"
WHITE      = "#FFFFFF"
LIGHT_GREY = "#F5F5F5"
MID_GREY   = "#E0E0E0"

TIER_COLORS = {
    "F1":  ("#2E7D32", WHITE),   # green
    "F2":  ("#0095A8", WHITE),   # teal
    "F3a": ("#E64A19", WHITE),   # dark orange — addressable (CC.2)
    "F3f": ("#B71C1C", WHITE),   # dark red — fundamental construct (CC.1)
}

# ---------------------------------------------------------------------------
# Figure
# ---------------------------------------------------------------------------
fig_height = 5.5
fig, ax = plt.subplots(figsize=(14.0, fig_height))
ax.set_axis_off()

fig.suptitle(
    "Table 7: Pipeline Output — AI Harmonization Verdicts with Reasoning",
    fontsize=10, fontweight="bold", color=NAVY,
    x=0.5, y=0.97, ha="center",
)

# Column widths (proportional fractions)
col_widths = [0.21, 0.21, 0.04, 0.06, 0.05, 0.36]

header_colours = [[NAVY] * len(HEADER)]

cell_colours = []
for i, tier_key in enumerate(ROW_TIER_KEYS):
    tier_bg, _ = TIER_COLORS[tier_key]
    row_bg = WHITE if i % 2 == 0 else LIGHT_GREY
    # Col 2 (Tier) gets tier color; all others get alternating row background
    cell_colours.append([row_bg, row_bg, tier_bg, row_bg, row_bg, row_bg])

tbl = ax.table(
    cellText=ROWS,
    colLabels=HEADER,
    colWidths=col_widths,
    cellColours=cell_colours,
    colColours=header_colours[0],
    loc="center",
    bbox=[0, 0.05, 1, 0.89],
)

tbl.auto_set_font_size(False)
tbl.set_fontsize(7.5)

# Header styling
for col in range(len(HEADER)):
    cell = tbl[0, col]
    cell.set_text_props(color=WHITE, fontweight="bold")
    cell.set_edgecolor(NAVY)
    cell.set_linewidth(1.0)
    cell.PAD = 0.06

# Body cell styling
for row_idx, tier_key in enumerate(ROW_TIER_KEYS):
    _, tier_fg = TIER_COLORS[tier_key]
    for col in range(len(HEADER)):
        cell = tbl[row_idx + 1, col]
        cell.set_edgecolor(MID_GREY)
        cell.set_linewidth(0.5)
        cell.PAD = 0.06
        if col == 2:  # Tier column
            cell.set_text_props(color=tier_fg, fontweight="bold", ha="center")
        elif col in (3, 4):  # Barrier, Conf. — centered
            cell.set_text_props(color="#222222", ha="center")
        else:
            cell.set_text_props(color="#222222", ha="left")

# Row heights
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_height(0.10)
    else:
        cell.set_height(0.185)

# ---------------------------------------------------------------------------
# Footnote
# ---------------------------------------------------------------------------
fig.text(
    0.01, 0.01,
    "NHB.0 = no barrier  |  CC.4 = construct scope  |  CC.2 = construct precision  |  CC.1 = fundamental construct mismatch\n"
    "Pair IDs: CPS_0858 (F1-A), CPS_0962 (F1-B), CPS_0212 (F2-A), CPS_0040 (F3 hours), CPS_0186 (F3 unemployment).  "
    "Reasoning from Stage 2 AI rater (claude-haiku-4-5). Final verdicts from Stage 3 arbitration.",
    fontsize=6.0, color="#546E7A", style="italic",
    ha="left", va="bottom",
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)

plt.savefig(out_dir / "fig07_verdict_examples.pdf", bbox_inches="tight", dpi=FIGURE_DPI)
plt.savefig(out_dir / "fig07_verdict_examples.png", bbox_inches="tight", dpi=FIGURE_DPI)
print(f"Saved: {out_dir / 'fig07_verdict_examples.pdf'}")
print(f"Saved: {out_dir / 'fig07_verdict_examples.png'}")
