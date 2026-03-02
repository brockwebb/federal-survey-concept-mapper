"""fig04_harmonizable_by_topic.py — Harmonizable questions by topic, CPS vs FoodAPS.

Grouped horizontal bars showing only the harmonizable counts per topic.
Replaces tables 6 (ch5) and 7 (ch6 subtopic detail) with a single visual.

Data from NUMBERS_MAP Step 7.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --- Data from NUMBERS_MAP Step 7 ---
topics =     ["Economic", "Social", "Demographic", "Housing"]
cps_harm =   [56, 11, 19, 0]
food_harm =  [36, 11,  8, 1]

# Colors (xdgov Data Design Standards)
NAVY = "#112E51"
TEAL = "#0095A8"

bar_height = 0.35
y = np.arange(len(topics))

fig, ax = plt.subplots(figsize=(7.5, 3.5))

bars1 = ax.barh(y - bar_height/2 - 0.02, cps_harm, bar_height, color=NAVY, alpha=0.85, label="CPS")
bars2 = ax.barh(y + bar_height/2 + 0.02, food_harm, bar_height, color=TEAL, alpha=0.85, label="FoodAPS")

# Labels at end of bars
for bar, val in zip(bars1, cps_harm):
    if val > 0:
        ax.text(val + 1, bar.get_y() + bar.get_height()/2, str(val),
                va="center", ha="left", fontsize=9, fontweight="bold", color=NAVY)

for bar, val in zip(bars2, food_harm):
    if val > 0:
        ax.text(val + 1, bar.get_y() + bar.get_height()/2, str(val),
                va="center", ha="left", fontsize=9, fontweight="bold", color=TEAL)

# Dash for CPS Housing (zero)
ax.text(1, bars1[3].get_y() + bars1[3].get_height()/2, "\u2014",
        va="center", ha="left", fontsize=9, color="#999999")

ax.set_yticks(y)
ax.set_yticklabels(topics, fontsize=10, fontweight="bold", color="#333333")
ax.invert_yaxis()
ax.set_xlim(0, 68)
ax.set_xlabel("Harmonizable questions (bridge variable candidates)", fontsize=9, color="#546E7A")
ax.tick_params(axis="x", colors="#546E7A", labelsize=8)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", length=0)

ax.legend(loc="lower right", fontsize=9, frameon=True, fancybox=True, framealpha=0.9)

# Totals annotation
ax.text(64, -0.7, "CPS: 86 total    FoodAPS: 56 total    Combined: 142",
        ha="right", va="center", fontsize=8, color="#546E7A", style="italic")

plt.tight_layout()

# Save
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(out_dir / "fig04_harmonizable_by_topic.pdf", bbox_inches="tight", dpi=300)
plt.savefig(out_dir / "fig04_harmonizable_by_topic.png", bbox_inches="tight", dpi=300)
print(f"Saved: {out_dir / 'fig04_harmonizable_by_topic.pdf'}")
