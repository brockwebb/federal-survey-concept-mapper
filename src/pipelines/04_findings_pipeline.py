#!/usr/bin/env python3
"""
04_findings_pipeline.py - Question-Level Consolidability Analysis

Part of Report 03: Harmonization Constraints
Stage 4 (Findings): Aggregates pair-level arbitration verdicts to question-level
consolidability metrics.

Core insight: Stakeholders need question-level answers ("Of CPS's N questions,
how many have at least one consolidable ACS match?"), not pair-level rates.

Usage:
    python 04_findings_pipeline.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

# Add scripts/ to path for lib imports
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.io_utils import load_config, ensure_dir, load_merged_csv
from lib.taxonomy import BARRIER_L1, FEASIBILITY_LEVELS

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

# Path setup for post-restructure layout
OUTPUT_DIR = REPO_ROOT / "output" / "report_03" / "analysis"


# ---------------------------------------------------------------------------
# Step 1: Load and join data
# ---------------------------------------------------------------------------

def load_data():
    """Load verdicts and question mappings, join them."""
    verdicts = pd.read_csv(OUTPUT_DIR / "final_verdicts.csv")
    log.info(f"Loaded {len(verdicts)} verdict rows")

    cps_map = load_merged_csv(REPO_ROOT / "data" / "processed" / "cps_comparison_merged.csv")
    foodaps_map = load_merged_csv(REPO_ROOT / "data" / "processed" / "foodaps_comparison_merged.csv")

    # Select mapping columns
    map_cols = ['pair_id', 'survey_q_id', 'survey_text', 'acs_q_id', 'acs_text', 'subtopic']
    question_map = pd.concat([cps_map[map_cols], foodaps_map[map_cols]], ignore_index=True)
    log.info(f"Combined question map: {len(question_map)} rows "
             f"({len(cps_map)} CPS + {len(foodaps_map)} FoodAPS)")

    # Join verdicts with question mapping
    pair_analysis = verdicts.merge(question_map, on='pair_id', how='left')

    # Check for unmatched pairs
    unmatched = pair_analysis['survey_q_id'].isna().sum()
    if unmatched > 0:
        log.warning(f"{unmatched} verdict rows have no question mapping")

    return pair_analysis


# ---------------------------------------------------------------------------
# Step 2: Define consolidability flags
# ---------------------------------------------------------------------------

def add_consolidability_flags(df):
    """Add boolean consolidability columns."""
    df['is_f1'] = df['final_feasibility'] == 'F1'
    df['is_f2'] = df['final_feasibility'] == 'F2'
    df['is_f3'] = df['final_feasibility'] == 'F3'
    df['is_consolidable'] = df['final_feasibility'].isin(['F1', 'F2'])
    return df


# ---------------------------------------------------------------------------
# Step 3: Aggregate to question-level
# ---------------------------------------------------------------------------

def aggregate_to_question_level(pair_analysis):
    """Aggregate pair-level results to one row per source question."""
    grouped = pair_analysis.groupby(['survey', 'survey_q_id'])

    question_level = grouped.agg(
        pair_count=('pair_id', 'count'),
        has_any_f1=('is_f1', 'any'),
        has_any_f2=('is_f2', 'any'),
        all_f3=('is_f3', 'all'),
        has_consolidable_path=('is_consolidable', 'any'),
        question_text=('survey_text', 'first'),
        best_feasibility=('final_feasibility', lambda x: min(x, key=lambda v: ['F1', 'F2', 'F3'].index(v) if v in ['F1', 'F2', 'F3'] else 99)),
    ).reset_index()

    # Derived: best_is_f2 = has F2 path but no F1 path
    question_level['best_is_f2'] = question_level['has_any_f2'] & ~question_level['has_any_f1']

    # Rename for clarity
    question_level.rename(columns={'has_any_f1': 'has_f1_path'}, inplace=True)

    log.info(f"Question-level: {len(question_level)} unique source questions")
    return question_level


# ---------------------------------------------------------------------------
# Step 4: Compute survey-level summary
# ---------------------------------------------------------------------------

def compute_survey_summary(question_level):
    """Compute per-survey consolidability summary."""
    summary = {}
    for survey, grp in question_level.groupby('survey'):
        n = len(grp)
        n_consolidable = int(grp['has_consolidable_path'].sum())
        n_f1 = int(grp['has_f1_path'].sum())
        n_f2_only = int(grp['best_is_f2'].sum())
        n_f3 = int(grp['all_f3'].sum())

        summary[survey] = {
            'total_questions': n,
            'consolidable_questions': n_consolidable,
            'consolidation_rate': round(n_consolidable / n, 4) if n > 0 else 0,
            'direct_f1_questions': n_f1,
            'direct_f1_rate': round(n_f1 / n, 4) if n > 0 else 0,
            'conditional_f2_questions': n_f2_only,
            'conditional_f2_rate': round(n_f2_only / n, 4) if n > 0 else 0,
            'not_consolidable_f3_questions': n_f3,
            'not_consolidable_f3_rate': round(n_f3 / n, 4) if n > 0 else 0,
        }

        log.info(f"{survey}: {n_consolidable}/{n} ({summary[survey]['consolidation_rate']:.1%}) "
                 f"consolidable (F1={n_f1}, F2-only={n_f2_only}, F3={n_f3})")

    return summary


# ---------------------------------------------------------------------------
# Step 5: Topic/domain analysis
# ---------------------------------------------------------------------------

def compute_topic_breakdown(pair_analysis):
    """Consolidation rates by subtopic/domain."""
    topic_stats = pair_analysis.groupby(['survey', 'subtopic']).agg(
        total_pairs=('pair_id', 'count'),
        consolidable_pairs=('is_consolidable', 'sum'),
        f1_pairs=('is_f1', 'sum'),
        f2_pairs=('is_f2', 'sum'),
        f3_pairs=('is_f3', 'sum'),
    ).reset_index()

    topic_stats['consolidation_rate'] = (
        topic_stats['consolidable_pairs'] / topic_stats['total_pairs']
    ).round(4)

    topic_stats = topic_stats.sort_values(['survey', 'consolidation_rate'],
                                          ascending=[True, False])
    return topic_stats


def compute_barrier_patterns(pair_analysis):
    """For F3 pairs, what barriers prevent consolidation?"""
    f3_pairs = pair_analysis[pair_analysis['is_f3']].copy()

    barrier_stats = f3_pairs.groupby(['survey', 'final_L1']).agg(
        count=('pair_id', 'count'),
    ).reset_index()

    # Add L1 descriptions
    barrier_stats['barrier_name'] = barrier_stats['final_L1'].map(BARRIER_L1)

    # Add percentage within survey
    survey_totals = barrier_stats.groupby('survey')['count'].transform('sum')
    barrier_stats['pct_of_f3'] = (barrier_stats['count'] / survey_totals).round(4)

    barrier_stats = barrier_stats.sort_values(['survey', 'count'], ascending=[True, False])
    return barrier_stats


# ---------------------------------------------------------------------------
# Step 6: F2 transformation inventory
# ---------------------------------------------------------------------------

def compute_f2_inventory(pair_analysis):
    """Inventory of F2 pairs with barrier types for planning statistical adjustments."""
    f2_pairs = pair_analysis[pair_analysis['final_feasibility'] == 'F2'].copy()

    cols = ['pair_id', 'survey', 'survey_q_id', 'survey_text', 'acs_q_id', 'acs_text',
            'final_L1', 'final_barrier_code', 'subtopic', 'confidence']
    # Only keep columns that exist
    cols = [c for c in cols if c in f2_pairs.columns]

    return f2_pairs[cols].sort_values(['survey', 'final_L1', 'pair_id'])


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(survey_summary, question_level, topic_breakdown, barrier_patterns,
                    f2_inventory, pair_analysis):
    """Generate human-readable findings report."""
    lines = []
    now = datetime.now().isoformat()

    lines.append("# Stage 4: Question-Level Consolidability Findings")
    lines.append(f"\n**Generated:** {now}")
    lines.append("")

    # --- Executive Summary ---
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("This analysis answers the core research question: **What proportion of source "
                 "survey questions can be consolidated with ACS?**")
    lines.append("")
    lines.append("Consolidability is determined at the *question* level — a source question is "
                 "consolidable if it has **at least one** ACS pair rated F1 (direct recode) or "
                 "F2 (statistical adjustment).")
    lines.append("")

    for survey, stats in sorted(survey_summary.items()):
        rate_pct = stats['consolidation_rate'] * 100
        f1_pct = stats['direct_f1_rate'] * 100
        f2_pct = stats['conditional_f2_rate'] * 100
        f3_pct = stats['not_consolidable_f3_rate'] * 100
        lines.append(f"### {survey}")
        lines.append(f"- **{stats['consolidable_questions']}/{stats['total_questions']} "
                     f"({rate_pct:.1f}%) questions have at least one consolidable path to ACS**")
        lines.append(f"  - Direct recode (F1): {stats['direct_f1_questions']} ({f1_pct:.1f}%)")
        lines.append(f"  - Statistical adjustment (F2): {stats['conditional_f2_questions']} ({f2_pct:.1f}%)")
        lines.append(f"  - Not consolidable (F3): {stats['not_consolidable_f3_questions']} ({f3_pct:.1f}%)")
        lines.append("")

    # --- Pair vs Question comparison ---
    lines.append("## Pair-Level vs Question-Level Rates")
    lines.append("")
    lines.append("Pair-level consolidability rates understate the true consolidation potential "
                 "because each source question is paired with multiple ACS questions, most of "
                 "which are unrelated.")
    lines.append("")
    lines.append("| Survey | Pair-Level Rate | Question-Level Rate | Unique Questions | Total Pairs |")
    lines.append("|--------|----------------|--------------------|-----------------:|------------:|")

    for survey, stats in sorted(survey_summary.items()):
        survey_pairs = pair_analysis[pair_analysis['survey'] == survey]
        pair_rate = survey_pairs['is_consolidable'].mean()
        lines.append(f"| {survey} | {pair_rate:.1%} | {stats['consolidation_rate']:.1%} "
                     f"| {stats['total_questions']} | {len(survey_pairs)} |")
    lines.append("")

    # --- Barrier distribution for F3 ---
    lines.append("## Barriers to Consolidation (F3 Pairs)")
    lines.append("")
    lines.append("Among pairs rated not consolidable (F3), the dominant barrier types are:")
    lines.append("")

    for survey in sorted(barrier_patterns['survey'].unique()):
        bp = barrier_patterns[barrier_patterns['survey'] == survey]
        lines.append(f"### {survey}")
        lines.append("")
        lines.append("| Barrier | Description | Count | % of F3 |")
        lines.append("|---------|-------------|------:|--------:|")
        for _, row in bp.iterrows():
            lines.append(f"| {row['final_L1']} | {row['barrier_name']} "
                         f"| {int(row['count'])} | {row['pct_of_f3']:.1%} |")
        lines.append("")

    # --- Top consolidable topics ---
    lines.append("## Topic Analysis")
    lines.append("")
    lines.append("Consolidation rates by subtopic (pair-level):")
    lines.append("")

    for survey in sorted(topic_breakdown['survey'].unique()):
        tb = topic_breakdown[topic_breakdown['survey'] == survey].head(15)
        lines.append(f"### {survey} — Top subtopics by consolidation rate")
        lines.append("")
        lines.append("| Subtopic | Total Pairs | Consolidable | Rate |")
        lines.append("|----------|------------:|-------------:|-----:|")
        for _, row in tb.iterrows():
            lines.append(f"| {row['subtopic']} | {int(row['total_pairs'])} "
                         f"| {int(row['consolidable_pairs'])} | {row['consolidation_rate']:.1%} |")
        lines.append("")

    # --- F2 summary ---
    lines.append("## F2 Transformation Requirements")
    lines.append("")
    n_f2 = len(f2_inventory)
    if n_f2 > 0:
        f2_by_barrier = f2_inventory.groupby(['survey', 'final_L1']).size().reset_index(name='count')
        lines.append(f"There are **{n_f2} pairs** rated F2 (statistical adjustment needed).")
        lines.append("Barrier types requiring transformation:")
        lines.append("")
        lines.append("| Survey | Barrier | Count |")
        lines.append("|--------|---------|------:|")
        for _, row in f2_by_barrier.iterrows():
            desc = BARRIER_L1.get(row['final_L1'], '')
            lines.append(f"| {row['survey']} | {row['final_L1']} ({desc}) | {int(row['count'])} |")
        lines.append("")
    else:
        lines.append("No F2 pairs found.")
        lines.append("")

    # --- Burden reduction ---
    lines.append("## Burden Reduction Potential")
    lines.append("")
    lines.append("If consolidable questions could be replaced by ACS equivalents:")
    lines.append("")
    for survey, stats in sorted(survey_summary.items()):
        lines.append(f"- **{survey}:** {stats['consolidable_questions']} of "
                     f"{stats['total_questions']} questions could potentially be eliminated "
                     f"({stats['consolidation_rate']:.1%})")
    lines.append("")
    lines.append("*Caveat: This is an upper bound. Practical consolidation depends on "
                 "use case, statistical precision requirements, and institutional constraints.*")
    lines.append("")

    # --- Methodology note ---
    lines.append("---")
    lines.append("")
    lines.append("**Methodology:** Pair-level feasibility verdicts from Stage 3 arbitration "
                 "(3 LLM arbitrators with majority-rule consolidation). Question-level "
                 "consolidability = at least one pair rated F1 or F2.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate(question_level, survey_summary):
    """Run sanity checks from the task spec."""
    errors = []

    # Check: consolidable + not_consolidable = total
    for _, row in question_level.iterrows():
        if row['has_consolidable_path'] == row['all_f3']:
            errors.append(f"{row['survey_q_id']}: has_consolidable_path == all_f3 (both {row['has_consolidable_path']})")

    # Check: per-survey sums add up
    for survey, stats in survey_summary.items():
        f1_f2_f3 = stats['direct_f1_questions'] + stats['conditional_f2_questions'] + stats['not_consolidable_f3_questions']
        if f1_f2_f3 != stats['total_questions']:
            errors.append(f"{survey}: F1({stats['direct_f1_questions']}) + F2({stats['conditional_f2_questions']}) "
                          f"+ F3({stats['not_consolidable_f3_questions']}) = {f1_f2_f3} != total({stats['total_questions']})")

    if errors:
        for e in errors:
            log.error(f"Validation error: {e}")
        raise ValueError(f"{len(errors)} validation errors")

    log.info("All validation checks passed")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=== Stage 4: Question-Level Consolidability Analysis ===")
    ensure_dir(OUTPUT_DIR)

    # Step 1: Load and join
    pair_analysis = load_data()

    # Step 2: Add flags
    pair_analysis = add_consolidability_flags(pair_analysis)

    # Step 3: Aggregate to question-level
    question_level = aggregate_to_question_level(pair_analysis)

    # Step 4: Survey summary
    survey_summary = compute_survey_summary(question_level)

    # Step 5: Topic and barrier analysis
    topic_breakdown = compute_topic_breakdown(pair_analysis)
    barrier_patterns = compute_barrier_patterns(pair_analysis)

    # Step 6: F2 inventory
    f2_inventory = compute_f2_inventory(pair_analysis)

    # Validate
    validate(question_level, survey_summary)

    # --- Write outputs ---
    # 1. Question-level CSV
    ql_path = OUTPUT_DIR / "stage4_question_level.csv"
    out_cols = ['survey', 'survey_q_id', 'question_text', 'pair_count',
                'has_consolidable_path', 'has_f1_path', 'best_is_f2', 'all_f3',
                'best_feasibility']
    question_level[out_cols].to_csv(ql_path, index=False)
    log.info(f"Wrote {ql_path}")

    # 2. Survey summary JSON
    ss_path = OUTPUT_DIR / "stage4_survey_summary.json"
    with open(ss_path, 'w') as f:
        json.dump(survey_summary, f, indent=2)
    log.info(f"Wrote {ss_path}")

    # 3. Findings report
    report = generate_report(survey_summary, question_level, topic_breakdown,
                             barrier_patterns, f2_inventory, pair_analysis)
    report_path = OUTPUT_DIR / "stage4_findings_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    log.info(f"Wrote {report_path}")

    # 4. Topic breakdown CSV
    tb_path = OUTPUT_DIR / "stage4_topic_breakdown.csv"
    topic_breakdown.to_csv(tb_path, index=False)
    log.info(f"Wrote {tb_path}")

    # 5. F2 transformations CSV
    f2_path = OUTPUT_DIR / "stage4_f2_transformations.csv"
    f2_inventory.to_csv(f2_path, index=False)
    log.info(f"Wrote {f2_path}")

    # 6. Barrier patterns CSV
    bp_path = OUTPUT_DIR / "stage4_barrier_patterns.csv"
    barrier_patterns.to_csv(bp_path, index=False)
    log.info(f"Wrote {bp_path}")

    log.info("=== Stage 4 complete ===")


if __name__ == '__main__':
    main()
