"""fig06_dob_examples.py — Date of birth / age: harmonization complexity spectrum.

Table showing how the same demographic variable (age/DOB) spans F1 through F3
depending on how it is operationalized. Source: docs/handoffs/birthdate_examples.md

Outputs: report/figures/fig06_dob_examples.pdf + .png
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
HEADER = ["Survey", "Source Question", "ACS Question", "Tier", "Barrier", "Note"]

ROWS = [
    [
        "FOODAPS",
        "What is your date\nof birth?",
        "What is Person N's age\nand date of birth?",
        "F1",
        "NHB.0",
        "Identical construct",
    ],
    [
        "CPS",
        "What is (name's/your)\ndate of birth?",
        "What is Person N's age\nand date of birth?",
        "F1–F2",
        "RS.1",
        "Compound vs single\nquestion",
    ],
    [
        "CPS",
        "Best guess as to how\nold on (your/his/her)\nlast birthday?",
        "What is Person N's age\nand date of birth?",
        "F2",
        "CC.2",
        "Off by up to\n364 days",
    ],
    [
        "CPS",
        "That would make (name/you)\napproximately AGE years old.\nIs that correct?",
        "What is Person N's age\nand date of birth?",
        "F3",
        "RS.1",
        "Verification probe,\nnot elicitation",
    ],
    [
        "CPS",
        "(Were/was) (name/you)\nborn a citizen of the\nUnited States?",
        "Is this person a citizen\nof the United States?",
        "F3",
        "CC.1",
        "Birthright vs\nany-path citizenship",
    ],
]

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY       = "#112E51"
WHITE      = "#FFFFFF"
LIGHT_GREY = "#F2F2F2"
MID_GREY   = "#E0E0E0"

TIER_COLORS = {
    "F1":    ("#2E7D32", WHITE),
    "F1–F2": ("#558B2F", WHITE),
    "F2":    ("#0095A8", WHITE),
    "F3":    ("#B71C1C", WHITE),
}

# ---------------------------------------------------------------------------
# Build figure
# ---------------------------------------------------------------------------
fig_height = 5.2
fig, ax = plt.subplots(figsize=(FIGURE_WIDTH + 3.0, fig_height))
ax.set_axis_off()

fig.suptitle(
    "Table 6: Date of Birth / Age — Harmonization Complexity Spectrum",
    fontsize=10, fontweight="bold", color=NAVY,
    x=0.5, y=0.97, ha="center",
)

# Column widths (fractions)
col_widths = [0.08, 0.22, 0.22, 0.07, 0.08, 0.20]

header_colours = [[NAVY] * len(HEADER)]

cell_colours = []
for i, row in enumerate(ROWS):
    tier_key = row[3]
    tier_bg, _ = TIER_COLORS[tier_key]
    row_bg = WHITE if i % 2 == 0 else LIGHT_GREY
    cell_colours.append([row_bg, row_bg, row_bg, tier_bg, row_bg, row_bg])

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
    tier_key = row[3]
    tier_bg, tier_fg = TIER_COLORS[tier_key]
    for col in range(len(HEADER)):
        cell = tbl[row_idx + 1, col]
        cell.set_edgecolor(MID_GREY)
        cell.set_linewidth(0.5)
        cell.PAD = 0.06
        if col == 3:
            cell.set_text_props(color=tier_fg, fontweight="bold", ha="center")
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
    "NHB.0 = no barrier  |  RS.1 = reference scope mismatch  |  "
    "CC.2 = construct precision difference  |  CC.1 = fundamental construct mismatch\n"
    "Same demographic concept (age) spans the full tier range depending on operationalization.",
    fontsize=6.5, color="#546E7A", style="italic",
    ha="left", va="bottom",
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)

plt.savefig(out_dir / "fig06_dob_examples.pdf", bbox_inches="tight", dpi=FIGURE_DPI)
plt.savefig(out_dir / "fig06_dob_examples.png", bbox_inches="tight", dpi=FIGURE_DPI)
print(f"Saved: {out_dir / 'fig06_dob_examples.pdf'}")
print(f"Saved: {out_dir / 'fig06_dob_examples.png'}")
