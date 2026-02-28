"""Figure 3: Topic composition of paired questions — ACS × CPS and ACS × FoodAPS.

Stacked horizontal bar showing the topic breakdown of questions that entered
the pairwise harmonization analysis. Three bars: ACS (combined), CPS, FoodAPS.

Source: docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv
Output: report/figures/fig03_paired_topic_composition.pdf
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
    position_stack,
    scale_fill_manual,
    scale_x_discrete,
)

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "assets"))
from census_plot_style import paper_theme, save_figure, TEXT_COLOR

# ---------------------------------------------------------------------------
# Census topic taxonomy — map subtopics to topics
# ---------------------------------------------------------------------------
SUBTOPIC_TO_TOPIC = {
    "Age": "Demographic",
    "Race": "Demographic",
    "Sex": "Demographic",
    "Hispanic Origin": "Demographic",
    "Citizenship": "Demographic",
    "Foreign Born": "Demographic",
    "Population": "Demographic",
    "Relationship": "Demographic",
    "Fertility": "Demographic",
    "Earnings": "Economic",
    "Employment Status": "Economic",
    "Hours/Week, Weeks/Year": "Economic",
    "Commissions": "Economic",
    "Occupation": "Economic",
    "Unemployment": "Economic",
    "Labor Force": "Economic",
    "Commute/Commuting": "Economic",
    "Health Insurance": "Economic",
    "Food Stamps (SNAP)": "Economic",
    "Costs (Mortgage, Taxes, Insurance)": "Economic",
    "Vehicles": "Economic",
    "Education": "Social",
    "School Enrollment": "Social",
    "Disability": "Social",
    "Veterans": "Social",
    "Marital Status": "Social",
    "Computer & Internet Use": "Social",
    "Household": "Demographic",  # Census taxonomy puts this under Demographic
    "Tenure (Own/Rent)": "Housing",
    "Rental": "Housing",
    "Migration": "Demographic",
    "Moving": "Demographic",
}

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
src = REPO / "docs/stages/03_harmonization/data/analysis/stage4_topic_breakdown.csv"
df = pd.read_csv(src)

# Map subtopics to topics
df["Topic"] = df["subtopic"].map(SUBTOPIC_TO_TOPIC)

# Fill any unmapped as "Other"
df["Topic"] = df["Topic"].fillna("Other")

# Aggregate: unique source questions per survey per topic
# Use total_pairs as a proxy is wrong — we need unique question counts.
# The stage4_topic_breakdown has pair-level data. For question counts,
# we approximate from the consolidation columns: a subtopic's question count
# is harder to extract here. Use total_pairs grouped by topic as relative weight.
# Actually: for a stacked bar showing "what topics are these surveys measuring",
# the pair counts per topic serve the visual purpose. Label as "Question Pairs".

topic_survey = (
    df.groupby(["survey", "Topic"])["total_pairs"]
    .sum()
    .reset_index()
    .rename(columns={"total_pairs": "Pairs"})
)

# Topic order (by overall frequency)
topic_totals = topic_survey.groupby("Topic")["Pairs"].sum().sort_values(ascending=False)
topic_order = topic_totals.index.tolist()
topic_survey["Topic"] = pd.Categorical(
    topic_survey["Topic"], categories=reversed(topic_order), ordered=True
)

# Survey order
topic_survey["Survey"] = pd.Categorical(
    topic_survey["survey"].map({"CPS": "CPS", "FOODAPS": "FoodAPS"}),
    categories=["FoodAPS", "CPS"],
    ordered=True,
)

# Census palette for topics
TOPIC_COLORS = {
    "Economic": "#112E51",    # navy
    "Social": "#FF7043",      # orange
    "Demographic": "#0095A8", # teal
    "Housing": "#78909C",     # grey
    "Other": "#AAAAAA",
}

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
p = (
    ggplot(topic_survey, aes(x="Survey", y="Pairs", fill="Topic"))
    + geom_bar(stat="identity", position="stack", width=0.7)
    + coord_flip()
    + scale_fill_manual(values=TOPIC_COLORS)
    + labs(
        title="Topic Composition of Evaluated Question Pairs",
        subtitle="CPS–ACS (1,030 pairs) and FoodAPS–ACS (568 pairs)",
        x="",
        y="Question Pairs Evaluated",
        fill="Topic",
    )
    + paper_theme(figure_size=(6.5, 3.0))
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
save_figure(p, "fig03_paired_topic_composition.pdf", REPO / "report" / "figures")
