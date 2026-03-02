#!/usr/bin/env python3
"""
Generate Figure 1: Topic Distribution (horizontal bar chart).

Horizontal bars showing the percentage breakdown of 6,954 classified
questions across five Census topic areas, sorted largest to smallest.
Labels show percentage and count at the end of each bar.

Input:  NUMBERS_MAP Step 2 topic distribution (validated source)
Output: report/figures/fig01_topic_distribution.pdf
        report/figures/fig01_topic_distribution.png

Colors: xdgov Data Design Standards via topic_colors.py
"""

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use("Agg")

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from topic_colors import TOPIC_COLORS, FIGURE_WIDTH, FIGURE_DPI

# --- Data (from NUMBERS_MAP Step 2, validated) ---
# Source: docs/stages/01_classification/data/comparison/topic_distribution.csv
TOPICS = [
    ("Economic",    42.8, 2980),
    ("Social",      35.5, 2467),
    ("Housing",     13.9, 967),
    ("Demographic",  5.3, 369),
    ("Government",   2.4, 167),
]

OUTPUT_DIR = Path(__file__).parent.parent.parent / "report" / "figures"


def create_figure():
    # Reverse for bottom-to-top (largest at top)
    topics_plot = list(reversed(TOPICS))

    fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, 2.4))

    names = [t[0] for t in topics_plot]
    pcts = [t[1] for t in topics_plot]
    colors = [TOPIC_COLORS[t[0]] for t in topics_plot]

    bars = ax.barh(names, pcts, height=0.6, color=colors, edgecolor="none")

    # Labels at end of each bar: percentage and count
    for bar, (name, pct, count) in zip(bars, topics_plot):
        ax.text(bar.get_width() + 0.8, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%  ({count:,})",
                ha="left", va="center", fontsize=9, fontfamily="serif", color="#4B636E")

    ax.set_xlim(0, 55)
    ax.set_xlabel("Percentage of classified questions (N = 6,954)", fontsize=10, fontfamily="serif")
    ax.tick_params(axis="y", labelsize=10)
    ax.tick_params(axis="x", labelsize=9)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for label in ax.get_yticklabels():
        label.set_fontfamily("serif")

    plt.tight_layout()
    return fig


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig = create_figure()

    out_pdf = OUTPUT_DIR / "fig01_topic_distribution.pdf"
    out_png = OUTPUT_DIR / "fig01_topic_distribution.png"

    fig.savefig(out_pdf, dpi=FIGURE_DPI, bbox_inches="tight")
    fig.savefig(out_png, dpi=FIGURE_DPI, bbox_inches="tight")
    plt.close()

    print(f"Saved: {out_pdf}")
    print(f"Saved: {out_png}")


if __name__ == "__main__":
    main()
