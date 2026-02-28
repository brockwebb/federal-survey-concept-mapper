"""Figure 1: Topic distribution across all classified questions.

Horizontal bar chart showing the 5 Census topic categories.
Data: average of two classifier models (GPT-5-mini, Claude Haiku 4.5).

Source: docs/stages/01_classification/data/comparison/topic_distribution.csv
Output: report/figures/fig01_topic_distribution.pdf
"""

import sys
from pathlib import Path

import pandas as pd
from plotnine import (
    aes,
    geom_bar,
    geom_text,
    ggplot,
    coord_flip,
    labs,
    scale_fill_manual,
    scale_x_discrete,
)

# Add assets/ to path for census_plot_style import
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "assets"))
from census_plot_style import paper_theme, save_figure, TEXT_COLOR

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
src = REPO / "docs/stages/01_classification/data/comparison/topic_distribution.csv"
df = pd.read_csv(src)

# Average the two models
df["Count"] = ((df["OpenAI_Count"] + df["Claude_Count"]) / 2).round().astype(int)
df["Pct"] = ((df["OpenAI_Percent"] + df["Claude_Percent"]) / 2).round(1)

# Drop "Unknown" row (n=3, irrelevant)
df = df[df["Topic"] != "Unknown"].copy()

# Order by count descending (reversed for coord_flip)
topic_order = df.sort_values("Count")["Topic"].tolist()
df["Topic"] = pd.Categorical(df["Topic"], categories=topic_order, ordered=True)

# Census palette — single color (navy) since this is one dimension
NAVY = "#112E51"

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
p = (
    ggplot(df, aes(x="Topic", y="Count"))
    + geom_bar(stat="identity", fill=NAVY, width=0.7)
    + geom_text(
        aes(label="Count"),
        ha="left",
        nudge_y=40,
        size=9,
        color=TEXT_COLOR,
    )
    + coord_flip()
    + labs(
        title="Question Distribution by Census Topic",
        subtitle=f"N = {df['Count'].sum():,} classified questions (avg. of two models)",
        x="",
        y="Number of Questions",
    )
    + paper_theme(figure_size=(6.5, 3.5))
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
save_figure(p, "fig01_topic_distribution.pdf", REPO / "report" / "figures")
