"""fig02_acs_family.py — ACS family survey network with consolidation potential.

Shows ACS at center connected to 5 family surveys. Edge width = shared subtopic
intersections. Node annotations show consolidation rates for CPS and FoodAPS.

Data from NUMBERS_MAP Steps 3, 7.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# --- Data from NUMBERS_MAP ---
FAMILY = {
    "SIPP":    {"intersections": 577, "subtopics": 38, "top": "Health Insurance,\nEmployment, Household"},
    "AHS":     {"intersections": 460, "subtopics": 34, "top": "Structure, Utilities,\nPlumbing/Kitchen"},
    "CE":      {"intersections": 283, "subtopics": 30, "top": "Health Insurance,\nHousing Costs, Household"},
    "CPS":     {"intersections": 181, "subtopics": 25, "top": "Employment Status,\nEarnings, Hours/Weeks",
                "consolidable": 86, "total_paired": 157, "rate": 54.8},
    "FoodAPS": {"intersections": 123, "subtopics": 23, "top": "SNAP, Household,\nSchool Enrollment",
                "consolidable": 56, "total_paired": 118, "rate": 47.5},
}

# Colors (xdgov Data Design Standards)
NAVY = "#112E51"
TEAL = "#0095A8"
MID_GRAY = "#B0B0B0"

# Layout: ACS at center, family surveys evenly spaced
angles = [90, 162, 234, 306, 18]
surveys = ["SIPP", "AHS", "CE", "CPS", "FoodAPS"]
RADIUS = 3.2

fig, ax = plt.subplots(figsize=(9, 8))
ax.set_xlim(-5.5, 5.5)
ax.set_ylim(-5.5, 5.5)
ax.set_aspect("equal")
ax.axis("off")

# ACS center node
acs_circle = plt.Circle((0, 0), 0.9, color=NAVY, zorder=10)
ax.add_patch(acs_circle)
ax.text(0, 0.15, "ACS", ha="center", va="center", fontsize=16, fontweight="bold",
        color="white", zorder=11)
ax.text(0, -0.25, "115 questions", ha="center", va="center", fontsize=8,
        color="white", zorder=11, style="italic")

# Draw edges and family nodes
for i, (survey, angle) in enumerate(zip(surveys, angles)):
    data = FAMILY[survey]
    rad = np.radians(angle)
    x = RADIUS * np.cos(rad)
    y = RADIUS * np.sin(rad)

    # Edge width proportional to intersections
    max_int = 577
    width = 1.5 + (data["intersections"] / max_int) * 6.5

    has_results = "rate" in data
    edge_color = TEAL if has_results else MID_GRAY
    edge_alpha = 0.7 if has_results else 0.4

    # Draw edge
    ax.plot([0, x], [0, y], color=edge_color, linewidth=width, alpha=edge_alpha,
            zorder=1, solid_capstyle="round")

    # Edge label (intersection count)
    mid_x = x * 0.48
    mid_y = y * 0.48
    ax.text(mid_x, mid_y, str(data["intersections"]),
            ha="center", va="center", fontsize=8, fontweight="bold",
            color=edge_color,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.9),
            zorder=5)

    # Survey node
    node_color = NAVY if has_results else "#546E7A"
    circle = plt.Circle((x, y), 0.75, color=node_color, zorder=10)
    ax.add_patch(circle)
    ax.text(x, y + 0.1, survey, ha="center", va="center", fontsize=13, fontweight="bold",
            color="white", zorder=11)
    ax.text(x, y - 0.22, f"{data['subtopics']} subtopics", ha="center", va="center",
            fontsize=7, color="white", zorder=11, style="italic")

    # Consolidation annotation (only for evaluated surveys)
    if has_results:
        if survey == "CPS":
            ann_x, ann_y = x + 0.3, y - 1.8
        else:  # FoodAPS
            ann_x, ann_y = x + 1.5, y - 1.2
        rate_text = f"{data['consolidable']}/{data['total_paired']} questions\nharmonizable ({data['rate']}%)"
        ax.annotate(rate_text,
                    xy=(x, y - 0.75),
                    xytext=(ann_x, ann_y),
                    fontsize=8, ha="center", va="top", color=NAVY,
                    fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.4", facecolor="#E8F5E9", edgecolor=TEAL,
                              linewidth=1.2, alpha=0.95),
                    arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.2),
                    zorder=12)

    # Top overlap areas
    dist = np.sqrt(x**2 + y**2)
    top_x = x + (x / dist) * 1.7
    top_y = y + (y / dist) * 1.4
    ax.text(top_x, top_y, data["top"], ha="center", va="center", fontsize=6.5,
            color="#546E7A", style="italic", zorder=6,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#E0E0E0",
                      linewidth=0.5, alpha=0.9))

# Legend
legend_elements = [
    mpatches.Patch(color=TEAL, alpha=0.7, label="Evaluated (CPS, FoodAPS)"),
    mpatches.Patch(color=MID_GRAY, alpha=0.4, label="Pending (SIPP, AHS, CE)"),
]
ax.legend(handles=legend_elements, loc="lower center", fontsize=8,
          frameon=True, fancybox=True, framealpha=0.9, ncol=2,
          bbox_to_anchor=(0.5, -0.02))

# Title
ax.set_title("ACS Family: Shared Subtopic Coverage and Harmonization Potential",
             fontsize=13, fontweight="bold", color=NAVY, pad=15)

# Subtitle
ax.text(0, -5.2,
        "Edge width proportional to shared subtopic intersections. Green annotations show evaluated harmonization rates.",
        ha="center", fontsize=7.5, color="#78909C", style="italic")

plt.tight_layout()

# Save
out_dir = Path(__file__).parent.parent.parent / "report" / "figures"
out_dir.mkdir(parents=True, exist_ok=True)
plt.savefig(out_dir / "fig02_acs_family.pdf", bbox_inches="tight", dpi=300)
plt.savefig(out_dir / "fig02_acs_family.png", bbox_inches="tight", dpi=300)
print(f"Saved: {out_dir / 'fig02_acs_family.pdf'}")
