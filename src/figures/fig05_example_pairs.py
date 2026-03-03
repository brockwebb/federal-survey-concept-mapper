"""fig05_example_pairs.py — Harmonization tier examples: one real question pair per tier.

Table rendered via matplotlib showing F1 / F2 / F3-addressable / F3-fundamental rows.
Source: docs/handoffs/example_pairs_candidates.md

Outputs: report/figures/fig05_example_pairs.pdf + .png
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Import shared constants
sys.path.insert(0, str(Path(__file__).parent))
from topic_colors import FIGURE_WIDTH, FIGURE_DPI

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
HEADER = ["Tier", "Survey", "Source Question", "ACS Question", "Barrier"]

ROWS = [
    [
        "F1",
        "CPS",
        "(Do you/Does NAME) have\ndifficulty dressing or bathing?",
        "Does this person have\ndifficulty dressing or bathing?",
        "NHB.0",
    ],
    [
        "F2",
        "CPS",
        "Did (name/you) ever serve on active\nduty in the U.S. Armed Forces?\nWhen did (you/he/she) serve?",
        "Has this person ever served on\nactive duty in Armed Forces,\nReserves, or National Guard?",
        "CC.4",
    ],
    [
        "F3\n(TC)",
        "CPS",
        "Now I have questions about the\nexact number of hours (name/you)\nworked LAST WEEK.",
        "How many hours do you usually\nwork per week at this rate?",
        "TC.2",
    ],
    [
        "F3\n(CC)",
        "CPS",
        "(Has name/you) been doing anything\nto find work during the last\n4 weeks?",
        "Has this person been informed\nthat he or she will be recalled\nto work within the next 6 months?",
        "CC.1",
    ],
]

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY      = "#112E51"
WHITE     = "#FFFFFF"
LIGHT_GREY = "#F2F2F2"
MID_GREY  = "#E0E0E0"

TIER_COLORS = {
    "F1":      ("#2E7D32", WHITE),   # green
    "F2":      ("#0095A8", WHITE),   # teal
    "F3\n(TC)": ("#E64A19", WHITE),  # dark orange
    "F3\n(CC)": ("#B71C1C", WHITE),  # dark red
}

# ---------------------------------------------------------------------------
# Build figure
# ---------------------------------------------------------------------------
fig_height = 4.6
fig, ax = plt.subplots(figsize=(FIGURE_WIDTH + 2.5, fig_height))
ax.set_axis_off()

fig.suptitle(
    "Table 5: Harmonization Tier Examples — Real Question Pairs",
    fontsize=10, fontweight="bold", color=NAVY,
    x=0.5, y=0.97, ha="center",
)

# Column widths (fractions summing to ~1)
col_widths = [0.07, 0.07, 0.33, 0.33, 0.07]

# Header colours
header_colours = [[NAVY] * len(HEADER)]

# Cell colours: tier column colour-coded, rest alternating
cell_colours = []
for i, row in enumerate(ROWS):
    tier_key = row[0]
    tier_bg, _ = TIER_COLORS[tier_key]
    row_bg = WHITE if i % 2 == 0 else LIGHT_GREY
    cell_colours.append([tier_bg, row_bg, row_bg, row_bg, row_bg])

tbl = ax.table(
    cellText=ROWS,
    colLabels=HEADER,
    colWidths=col_widths,
    cellColours=cell_colours,
    colColours=header_colours[0],
    loc="center",
    bbox=[0, 0, 1, 1],
)

tbl.auto_set_font_size(False)
tbl.set_fontsize(8)

# Style header
for col in range(len(HEADER)):
    cell = tbl[0, col]
    cell.set_text_props(color=WHITE, fontweight="bold")
    cell.set_edgecolor(NAVY)
    cell.set_linewidth(1.0)
    cell.PAD = 0.06

# Style body cells
for row_idx, row in enumerate(ROWS):
    tier_key = row[0]
    tier_bg, tier_fg = TIER_COLORS[tier_key]
    for col in range(len(HEADER)):
        cell = tbl[row_idx + 1, col]
        cell.set_edgecolor(MID_GREY)
        cell.set_linewidth(0.5)
        cell.PAD = 0.06
        if col == 0:
            cell.set_text_props(color=tier_fg, fontweight="bold", ha="center")
        else:
            cell.set_text_props(color="#222222", ha="left")

# Row heights — taller for F2/F3 rows that have 3-line text
row_heights = {1: 0.28, 2: 0.28, 3: 0.28, 4: 0.28}
for (r, c), cell in tbl.get_celld().items():
    if r == 0:
        cell.set_height(0.12)
    else:
        cell.set_height(0.20)

# ---------------------------------------------------------------------------
# Footnote
# ---------------------------------------------------------------------------
fig.text(
    0.01, 0.01,
    "NHB.0 = no barrier  |  CC.4 = construct scope difference  |  "
    "TC.2 = reference period mismatch  |  CC.1 = fundamental construct mismatch",
    fontsize=6.5, color="#546E7A", style="italic",
    ha="left", va="bottom",
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)

plt.savefig(out_dir / "fig05_example_pairs.pdf", bbox_inches="tight", dpi=FIGURE_DPI)
plt.savefig(out_dir / "fig05_example_pairs.png", bbox_inches="tight", dpi=FIGURE_DPI)
print(f"Saved: {out_dir / 'fig05_example_pairs.pdf'}")
print(f"Saved: {out_dir / 'fig05_example_pairs.png'}")
