"""Figure 2: Total questions per survey — ACS family.

Single horizontal bar chart showing the 6 ACS family surveys by total
question count. ACS highlighted as anchor.

Reads validated counts from docs/validation/question_counts.json.
Run src/validation/validate_question_counts.py first to generate that file.

Source: docs/validation/question_counts.json (derived from data/raw/PublicSurveyQuestionsMap.csv)
Output: report/figures/fig02_acs_family_profile.pdf
"""

import json
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
)

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "assets"))
from census_plot_style import paper_theme, save_figure, TEXT_COLOR

NAVY = "#112E51"
ORANGE = "#FF7043"

# ---------------------------------------------------------------------------
# Data — from validated counts
# ---------------------------------------------------------------------------
counts_path = REPO / "docs" / "validation" / "question_counts.json"
if not counts_path.exists():
    print(f"ERROR: {counts_path} not found.")
    print("Run: python src/validation/validate_question_counts.py")
    sys.exit(1)

with open(counts_path) as f:
    validated = json.load(f)

family = validated["acs_family_counts"]
df = pd.DataFrame([
    {"Survey": k, "Questions": v} for k, v in family.items()
])

# Order by count (ascending for coord_flip so largest is at top)
survey_order = df.sort_values("Questions")["Survey"].tolist()
df["Survey"] = pd.Categorical(df["Survey"], categories=survey_order, ordered=True)

# ACS highlighted
df["is_acs"] = df["Survey"] == "ACS"

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
p = (
    ggplot(df, aes(x="Survey", y="Questions", fill="is_acs"))
    + geom_bar(stat="identity", width=0.7)
    + geom_text(
        aes(label="Questions"),
        ha="left",
        nudge_y=20,
        size=9,
        color=TEXT_COLOR,
    )
    + coord_flip()
    + scale_fill_manual(values={True: ORANGE, False: NAVY}, guide=None)
    + labs(
        title="Total Questions by Survey — ACS Family",
        subtitle="ACS (orange) serves as the anchor for harmonization comparisons",
        x="",
        y="Number of Questions",
    )
    + paper_theme(figure_size=(6.5, 3.5))
)

# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------
save_figure(p, "fig02_acs_family_profile.pdf", REPO / "report" / "figures")
