"""fig02b_acs_family_horizontal.py — ACS family bridge diagram, 16:9 slide format.

Horizontal layout: ACS spine on left, 5 family surveys stacked on right.
Line width proportional to shared subtopic intersections. Slide-friendly
alternative to fig02_acs_family.py (radial, paper format).

Data from NUMBERS_MAP Steps 3, 7.
Outputs: report/figures/fig02b_acs_family_horizontal.pdf + .png
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).parent))
from topic_colors import FIGURE_DPI

plt.rcParams.update({"font.family": "sans-serif"})

# ---------------------------------------------------------------------------
# Data — NUMBERS_MAP Steps 3, 7
# Order: top to bottom by intersection count (descending)
# ---------------------------------------------------------------------------
SURVEYS = [
    {"name": "SIPP",    "intersections": 577, "subtopics": 38, "evaluated": False},
    {"name": "AHS",     "intersections": 460, "subtopics": 34, "evaluated": False},
    {"name": "CE",      "intersections": 283, "subtopics": 30, "evaluated": False},
    {"name": "CPS",     "intersections": 181, "subtopics": 25, "evaluated": True,
     "total_questions": 211, "consolidable": 86,  "total_paired": 157, "rate": 54.8},
    {"name": "FoodAPS", "intersections": 123, "subtopics": 23, "evaluated": True,
     "total_questions": 462, "consolidable": 56,  "total_paired": 118, "rate": 47.5},
]

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
NAVY      = "#112E51"
TEAL      = "#0095A8"
MID_GRAY  = "#B0B0B0"
DARK_GRAY = "#546E7A"
GREEN_BG  = "#E8F5E9"
WHITE     = "#FFFFFF"

# ---------------------------------------------------------------------------
# Canvas
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5.5))
ax.set_xlim(0, 14)
ax.set_ylim(0, 10)
ax.axis("off")

# ---------------------------------------------------------------------------
# Key x positions (data units)
# ---------------------------------------------------------------------------
ACS_LEFT,    ACS_RIGHT    = 0.5, 2.9   # ACS spine
SURVEY_LEFT, SURVEY_RIGHT = 7.0, 9.4   # survey node boxes
ANN_X                     = 9.65       # annotation box left edge

# ---------------------------------------------------------------------------
# Survey y centers — top (SIPP) to bottom (FoodAPS)
# ---------------------------------------------------------------------------
Y_TOP, Y_BOT = 8.5, 1.5
N = len(SURVEYS)
Y_CENTERS = [Y_TOP - i * (Y_TOP - Y_BOT) / (N - 1) for i in range(N)]

MAX_INT          = max(s["intersections"] for s in SURVEYS)
LW_MIN, LW_MAX   = 2.5, 11.0

# ---------------------------------------------------------------------------
# ACS spine (tall navy rectangle)
# ---------------------------------------------------------------------------
acs_box = FancyBboxPatch(
    (ACS_LEFT, 0.9), ACS_RIGHT - ACS_LEFT, 8.2,
    boxstyle="round,pad=0.12",
    facecolor=NAVY, edgecolor=NAVY, linewidth=0, zorder=5,
)
ax.add_patch(acs_box)

acs_cx = (ACS_LEFT + ACS_RIGHT) / 2
ax.text(acs_cx, 5.6, "ACS",
        ha="center", va="center", fontsize=22, fontweight="bold",
        color=WHITE, zorder=10)
ax.text(acs_cx, 4.6, "115 questions",
        ha="center", va="center", fontsize=9, color=WHITE,
        style="italic", zorder=10)
ax.text(acs_cx, 3.8, "anchor survey",
        ha="center", va="center", fontsize=8, color="#90B8D8",
        zorder=10)

# ---------------------------------------------------------------------------
# Connecting lines + survey nodes
# ---------------------------------------------------------------------------
node_cx = (SURVEY_LEFT + SURVEY_RIGHT) / 2
node_h  = 1.1

for survey, yc in zip(SURVEYS, Y_CENTERS):
    name      = survey["name"]
    n_int     = survey["intersections"]
    n_sub     = survey["subtopics"]
    evaluated = survey["evaluated"]

    lw         = LW_MIN + (n_int / MAX_INT) * (LW_MAX - LW_MIN)
    line_color = TEAL     if evaluated else MID_GRAY
    line_alpha = 0.82     if evaluated else 0.50
    node_color = NAVY     if evaluated else DARK_GRAY

    # Horizontal bridge line
    ax.plot([ACS_RIGHT, SURVEY_LEFT], [yc, yc],
            color=line_color, linewidth=lw, alpha=line_alpha,
            solid_capstyle="butt", zorder=2)

    # Survey node box
    node_box = FancyBboxPatch(
        (SURVEY_LEFT, yc - node_h / 2), SURVEY_RIGHT - SURVEY_LEFT, node_h,
        boxstyle="round,pad=0.1",
        facecolor=node_color, edgecolor=node_color, linewidth=0, zorder=7,
    )
    ax.add_patch(node_box)

    ax.text(node_cx, yc + 0.16, name,
            ha="center", va="center", fontsize=13, fontweight="bold",
            color=WHITE, zorder=10)
    if evaluated:
        node_sub = f"{survey['total_questions']} questions"
    else:
        node_sub = f"{n_sub} shared subtopics"
    ax.text(node_cx, yc - 0.30, node_sub,
            ha="center", va="center", fontsize=8, color=WHITE,
            style="italic", zorder=10)

    # Harmonization annotation (evaluated surveys only)
    if evaluated:
        ann_text = (f"{survey['consolidable']}/{survey['total_paired']} "
                    f"harmonizable  ({survey['rate']}%)")
        ax.text(ANN_X + 0.12, yc, ann_text,
                ha="left", va="center", fontsize=9.5,
                color=NAVY, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.4", facecolor=GREEN_BG,
                          edgecolor=TEAL, linewidth=1.3, alpha=0.97),
                zorder=12)

# ---------------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------------
ax.set_title(
    "ACS Family: Shared Subtopic Coverage and Harmonization Potential",
    fontsize=14, fontweight="bold", color=NAVY, pad=14,
)

# ---------------------------------------------------------------------------
# Legend and footnote
# ---------------------------------------------------------------------------
legend_elements = [
    mpatches.Patch(color=TEAL,     alpha=0.82, label="Evaluated (CPS, FoodAPS)"),
    mpatches.Patch(color=MID_GRAY, alpha=0.50, label="Pending (SIPP, AHS, CE)"),
]
ax.legend(handles=legend_elements, loc="lower left", fontsize=9,
          frameon=True, fancybox=True, framealpha=0.92,
          bbox_to_anchor=(0.01, 0.01))

ax.text(ACS_RIGHT + 0.3, 0.22,
        "Line width reflects relative concept overlap between surveys.",
        ha="left", va="center", fontsize=7.5, color="#78909C", style="italic")

plt.tight_layout()

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)

plt.savefig(out_dir / "fig02b_acs_family_horizontal.pdf", bbox_inches="tight", dpi=FIGURE_DPI)
plt.savefig(out_dir / "fig02b_acs_family_horizontal.png", bbox_inches="tight", dpi=FIGURE_DPI)
print(f"Saved: {out_dir / 'fig02b_acs_family_horizontal.pdf'}")
print(f"Saved: {out_dir / 'fig02b_acs_family_horizontal.png'}")
