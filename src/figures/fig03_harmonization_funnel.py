"""fig03_harmonization_funnel.py — Horizontal bar chart showing question funnel.

For each survey (CPS, FoodAPS): Total questions → ACS concept overlap → Harmonizable.
Replaces table 5 (results funnel) with a visual.

Data from NUMBERS_MAP Steps 4, 7.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --- Data from NUMBERS_MAP ---
surveys = ["CPS", "FoodAPS"]
total =       [211, 462]
overlap =     [157, 118]
harmonizable = [86,  56]

# Colors (xdgov Data Design Standards)
NAVY = "#112E51"
TEAL = "#0095A8"
GREEN = "#2E8B57"

colors = [NAVY, TEAL, GREEN]
labels = ["Total survey questions", "ACS concept overlap", "Harmonization paths"]

bar_height = 0.45
group_gap = 0.12
group_spacing = 1.0

fig, ax = plt.subplots(figsize=(7.5, 3.8))

for i, survey in enumerate(surveys):
    vals = [total[i], overlap[i], harmonizable[i]]
    group_top = i * (3 * (bar_height + group_gap) + group_spacing)
    for j, (val, color, label) in enumerate(zip(vals, colors, labels)):
        y = group_top + j * (bar_height + group_gap)
        ax.barh(y, val, height=bar_height, color=color, alpha=0.85,
                label=label if i == 0 else None)
        if j == 0:
            pct_text = f"{val}"
        elif j == 1:
            pct = val / total[i] * 100
            pct_text = f"{val} ({pct:.0f}%)"
        else:
            pct_of_overlap = val / overlap[i] * 100
            pct_text = f"{val} ({pct_of_overlap:.1f}% of paired)"
        ax.text(val + 5, y, pct_text, va="center", ha="left", fontsize=8.5,
                color=color, fontweight="bold")

    group_center = group_top + (bar_height + group_gap)
    ax.text(-12, group_center, survey, va="center", ha="right", fontsize=12,
            fontweight="bold", color=NAVY)

max_y = 1 * (3 * (bar_height + group_gap) + group_spacing) + 2 * (bar_height + group_gap) + bar_height
ax.set_xlim(0, 540)
ax.set_ylim(max_y + 0.3, -0.4)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.set_yticks([])
ax.set_xlabel("Number of questions", fontsize=9, color="#546E7A")
ax.tick_params(axis="x", colors="#546E7A", labelsize=8)

ax.legend(loc="upper right", fontsize=8, frameon=True, fancybox=True,
          framealpha=0.9, edgecolor="#E0E0E0")

plt.tight_layout()

# Save
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(out_dir / "fig03_harmonization_funnel.pdf", bbox_inches="tight", dpi=300)
plt.savefig(out_dir / "fig03_harmonization_funnel.png", bbox_inches="tight", dpi=300)
print(f"Saved: {out_dir / 'fig03_harmonization_funnel.pdf'}")
