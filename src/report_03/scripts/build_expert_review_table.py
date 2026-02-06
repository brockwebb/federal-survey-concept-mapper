#!/usr/bin/env python3
"""
build_expert_review_table.py - Create stakeholder expert review tables

For each source question: best ACS match, classification, barrier codes,
arbitrator reasoning, confidence, and triage quadrant.

Outputs:
  - expert_review_foodaps.csv
  - expert_review_cps.csv
  - expert_review_combined.csv
  - taxonomy_reference.md
  - classification_distribution.md

Usage:
    python scripts/build_expert_review_table.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from lib.io_utils import ensure_dir
from lib.taxonomy import BARRIER_L1, BARRIER_CODES

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "analysis"

# Subcode definitions (from taxonomy_v1.md)
SUBCODE_DEFS = {
    'TC.1': 'Reference period length',
    'TC.2': 'Temporal framing',
    'TC.3': 'Calendar alignment',
    'CC.1': 'Concept definition',
    'CC.2': 'Operationalization',
    'CC.3': 'Boundary conditions',
    'CC.4': 'Scope inclusions',
    'PC.1': 'Universe definition',
    'PC.2': 'Frame exclusions',
    'PC.3': 'Age bounds',
    'PC.4': 'Geographic scope',
    'RS.1': 'Scale type',
    'RS.2': 'Category structure',
    'RS.3': 'Anchoring/labels',
    'RS.4': 'Numeric vs verbal',
    'MC.1': 'Interview mode',
    'MC.2': 'Question routing',
    'MC.3': 'Contextual priming',
    'MC.4': 'Proxy response',
    'PM.1': 'Coding schemes',
    'PM.2': 'Derived variables',
    'PM.3': 'Documentation gaps',
    'NHB.0': 'No barrier',
}

FEASIBILITY_DEFS = {
    'F1': 'Directly Consolidable — questions measure same construct with compatible methods',
    'F2': 'Consolidable with Transformation — same construct, needs recoding/adjustment',
    'F3': 'Not Consolidable — different constructs or incompatible methods',
}

QUADRANT_DEFS = {
    'Q1': 'Confident consolidable (auto-accept)',
    'Q2': 'Confident non-consolidable (auto-reject)',
    'Q3': 'Edge case — leaning yes, contested (expert review)',
    'Q4': 'Ambiguous — low confidence both axes (expert review)',
}

TRIAGE_ORDER = {'Q3': 0, 'Q4': 1, 'Q1': 2, 'Q2': 3}


def build_expert_table():
    """Build the joined expert review table."""
    # Load best matches
    best = pd.read_csv(OUTPUT_DIR / "stage4_question_best_matches.csv")
    log.info(f"Best matches: {len(best)} rows")

    # Load final verdicts for confidence and barrier codes
    verdicts = pd.read_csv(OUTPUT_DIR / "final_verdicts.csv")

    # Load arbitration merged for reasoning
    arb = pd.read_csv(OUTPUT_DIR / "arbitration_merged.csv",
                       usecols=['pair_id',
                                'anthropic_reasoning', 'anthropic_specific_conflict',
                                'anthropic_final_barrier_code', 'anthropic_final_feasibility',
                                'openai_reasoning', 'openai_specific_conflict',
                                'openai_final_barrier_code', 'openai_final_feasibility',
                                'google_reasoning', 'google_specific_conflict',
                                'google_final_barrier_code', 'google_final_feasibility'])

    # Load source question mappings for full (untruncated) text
    from lib.io_utils import load_merged_csv
    cps_map = load_merged_csv(BASE_DIR / "data" / "cps_comparison_merged.csv")
    foodaps_map = load_merged_csv(BASE_DIR / "data" / "foodaps_comparison_merged.csv")
    map_cols = ['pair_id', 'survey_q_id', 'survey_text', 'acs_q_id', 'acs_text', 'subtopic']
    question_map = pd.concat([cps_map[map_cols], foodaps_map[map_cols]], ignore_index=True)

    # Join best matches with verdicts
    expert = best.merge(
        verdicts[['pair_id', 'confidence', 'final_L1', 'final_barrier_code']],
        on='pair_id', how='left'
    )

    # Join with arbitration reasoning
    expert = expert.merge(arb, on='pair_id', how='left')

    # Join with full question texts
    expert = expert.merge(
        question_map[['pair_id', 'survey_text', 'acs_text', 'subtopic']],
        on='pair_id', how='left', suffixes=('', '_full')
    )

    # Build combined reasoning (use the verdict-winning arbitrator's reasoning,
    # or combine all for transparency)
    def combine_reasoning(row):
        parts = []
        for arb_name in ['anthropic', 'openai', 'google']:
            r = row.get(f'{arb_name}_reasoning')
            if pd.notna(r) and str(r).strip():
                feas = row.get(f'{arb_name}_final_feasibility', '?')
                barrier = row.get(f'{arb_name}_final_barrier_code', '?')
                parts.append(f"[{arb_name.title()} — {feas}/{barrier}] {str(r).strip()}")
        return " ||| ".join(parts) if parts else ""

    expert['arbitrator_reasoning'] = expert.apply(combine_reasoning, axis=1)

    # Build specific conflict summary
    def combine_conflicts(row):
        parts = []
        for arb_name in ['anthropic', 'openai', 'google']:
            c = row.get(f'{arb_name}_specific_conflict')
            if pd.notna(c) and str(c).strip():
                parts.append(str(c).strip())
        # Deduplicate similar conflicts
        seen = set()
        unique = []
        for p in parts:
            key = p[:80].lower()
            if key not in seen:
                seen.add(key)
                unique.append(p)
        return " | ".join(unique) if unique else ""

    expert['specific_conflicts'] = expert.apply(combine_conflicts, axis=1)

    # Add barrier subcode description
    expert['barrier_description'] = expert['final_barrier_code'].map(SUBCODE_DEFS).fillna('')

    # Use full text if available, else keep truncated
    if 'survey_text' in expert.columns and 'survey_text_full' in expert.columns:
        expert['source_text_full'] = expert['survey_text_full'].fillna(expert['source_text'])
    else:
        expert['source_text_full'] = expert.get('survey_text', expert['source_text'])

    if 'acs_text' in expert.columns and 'acs_text_full' in expert.columns:
        expert['best_match_text_full'] = expert['acs_text_full'].fillna(expert['best_match_text'])
    else:
        expert['best_match_text_full'] = expert.get('acs_text', expert['best_match_text'])

    # Select and order output columns
    out_cols = [
        'survey', 'source_q_id', 'source_text_full',
        'best_match_q_id', 'best_match_text_full', 'subtopic',
        'best_feasibility', 'final_L1', 'final_barrier_code', 'barrier_description',
        'confidence', 'score_borda', 'score_entropy', 'triage_quadrant',
        'specific_conflicts', 'arbitrator_reasoning', 'pair_id'
    ]
    # Only keep columns that exist
    out_cols = [c for c in out_cols if c in expert.columns]
    expert = expert[out_cols]

    # Rename for stakeholder clarity
    expert = expert.rename(columns={
        'source_text_full': 'source_text',
        'best_match_text_full': 'best_match_text',
        'final_L1': 'barrier_category',
        'final_barrier_code': 'barrier_subcode',
    })

    # Sort: Q3/Q4 first (need expert review), then Q1, then Q2
    expert['_sort'] = expert['triage_quadrant'].map(TRIAGE_ORDER)
    expert = expert.sort_values(['survey', '_sort', 'score_borda'],
                                ascending=[True, True, False])
    expert = expert.drop(columns='_sort')

    return expert


def write_taxonomy_reference():
    """Write taxonomy_reference.md."""
    lines = []
    lines.append("# Classification Taxonomy Reference")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")

    lines.append("## Feasibility Codes")
    lines.append("")
    lines.append("| Code | Definition | Action |")
    lines.append("|------|-----------|--------|")
    actions = {
        'F1': 'Can substitute directly',
        'F2': 'Can substitute with documented transformation',
        'F3': 'Cannot substitute',
    }
    for code in ['F1', 'F2', 'F3']:
        lines.append(f"| {code} | {FEASIBILITY_DEFS[code]} | {actions[code]} |")
    lines.append("")

    lines.append("## Barrier Categories (L1)")
    lines.append("")
    lines.append("| Code | Name | Definition |")
    lines.append("|------|------|-----------|")
    for code, name in BARRIER_L1.items():
        lines.append(f"| {code} | {name} | See subcodes below |")
    lines.append("")

    lines.append("## Barrier Subcodes (L2)")
    lines.append("")
    lines.append("| Code | Name | Parent |")
    lines.append("|------|------|--------|")
    for code, name in sorted(SUBCODE_DEFS.items()):
        parent = code.split('.')[0]
        parent_name = BARRIER_L1.get(parent, '')
        lines.append(f"| {code} | {name} | {parent} ({parent_name}) |")
    lines.append("")

    lines.append("## Triage Quadrants")
    lines.append("")
    lines.append("| Quadrant | Description | Expert Review? |")
    lines.append("|----------|-------------|:-:|")
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        review = 'Yes' if q in ('Q3', 'Q4') else 'No'
        lines.append(f"| {q} | {QUADRANT_DEFS[q]} | {review} |")
    lines.append("")

    path = OUTPUT_DIR / "taxonomy_reference.md"
    with open(path, 'w') as f:
        f.write("\n".join(lines))
    log.info(f"Wrote {path}")


def write_classification_distribution(expert):
    """Write classification_distribution.md."""
    lines = []
    lines.append("# Classification Distribution Summary")
    lines.append(f"\n*Generated: {datetime.now().strftime('%Y-%m-%d')}*")
    lines.append("")

    # By survey
    lines.append("## By Survey and Feasibility")
    lines.append("")
    for survey in sorted(expert['survey'].unique()):
        s = expert[expert['survey'] == survey]
        n = len(s)
        lines.append(f"### {survey} (N={n} questions)")
        lines.append("")
        lines.append("| Feasibility | Count | % |")
        lines.append("|-------------|------:|--:|")
        for feas in ['F1', 'F2', 'F3']:
            cnt = (s['best_feasibility'] == feas).sum()
            pct = cnt / n * 100
            lines.append(f"| {feas} | {cnt} | {pct:.1f}% |")
        lines.append("")

    # By barrier code (F2 and F3 only)
    lines.append("## By Barrier Category (F2 and F3 only)")
    lines.append("")
    f2f3 = expert[expert['best_feasibility'].isin(['F2', 'F3'])]
    barrier_pivot = f2f3.groupby(['survey', 'barrier_category']).size().unstack(fill_value=0)
    surveys = sorted(expert['survey'].unique())

    lines.append("| Barrier | " + " | ".join(surveys) + " | Total |")
    lines.append("|---------|" + "|".join(["------:" for _ in surveys]) + "|------:|")
    for barrier in sorted(BARRIER_L1.keys()):
        vals = []
        total = 0
        for survey in surveys:
            cnt = int(barrier_pivot.loc[survey, barrier]) if survey in barrier_pivot.index and barrier in barrier_pivot.columns else 0
            vals.append(str(cnt))
            total += cnt
        if total > 0:
            lines.append(f"| {barrier} ({BARRIER_L1[barrier]}) | " + " | ".join(vals) + f" | {total} |")
    lines.append("")

    # By triage quadrant
    lines.append("## By Triage Quadrant")
    lines.append("")
    lines.append("| Quadrant | " + " | ".join(surveys) + " | Total | Expert Review |")
    lines.append("|----------|" + "|".join(["------:" for _ in surveys]) + "|------:|:---:|")
    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        vals = []
        total = 0
        for survey in surveys:
            cnt = int(((expert['survey'] == survey) & (expert['triage_quadrant'] == q)).sum())
            vals.append(str(cnt))
            total += cnt
        review = 'Yes' if q in ('Q3', 'Q4') else 'No'
        lines.append(f"| {q} | " + " | ".join(vals) + f" | {total} | {review} |")
    lines.append("")

    # Summary
    q3q4 = expert[expert['triage_quadrant'].isin(['Q3', 'Q4'])]
    lines.append(f"**Total needing expert review:** {len(q3q4)} questions ({len(q3q4)/len(expert)*100:.1f}%)")
    lines.append("")

    path = OUTPUT_DIR / "classification_distribution.md"
    with open(path, 'w') as f:
        f.write("\n".join(lines))
    log.info(f"Wrote {path}")


def main():
    log.info("=== Building Expert Review Tables ===")
    ensure_dir(OUTPUT_DIR)

    # Build table
    expert = build_expert_table()
    log.info(f"Expert review table: {len(expert)} rows, {len(expert.columns)} columns")

    # Split by survey
    foodaps = expert[expert['survey'] == 'FOODAPS'].copy()
    cps = expert[expert['survey'] == 'CPS'].copy()

    # Validate
    errors = []
    if len(cps) != 240:
        errors.append(f"CPS row count: {len(cps)} (expected 240)")
    if len(foodaps) != 140:
        errors.append(f"FoodAPS row count: {len(foodaps)} (expected 140)")
    if len(expert) != 380:
        errors.append(f"Combined row count: {len(expert)} (expected 380)")

    null_reasoning = expert['arbitrator_reasoning'].isna().sum() + (expert['arbitrator_reasoning'] == '').sum()
    if null_reasoning > 0:
        errors.append(f"{null_reasoning} rows missing arbitrator reasoning")

    if errors:
        for e in errors:
            log.error(f"Validation error: {e}")
        raise ValueError(f"{len(errors)} validation errors")

    log.info("All validation checks passed")

    # Save CSVs
    foodaps.to_csv(OUTPUT_DIR / "expert_review_foodaps.csv", index=False)
    log.info(f"Wrote expert_review_foodaps.csv ({len(foodaps)} rows)")

    cps.to_csv(OUTPUT_DIR / "expert_review_cps.csv", index=False)
    log.info(f"Wrote expert_review_cps.csv ({len(cps)} rows)")

    expert.to_csv(OUTPUT_DIR / "expert_review_combined.csv", index=False)
    log.info(f"Wrote expert_review_combined.csv ({len(expert)} rows)")

    # Write markdown outputs
    write_taxonomy_reference()
    write_classification_distribution(expert)

    # Summary
    for survey in sorted(expert['survey'].unique()):
        s = expert[expert['survey'] == survey]
        log.info(f"{survey}: {len(s)} questions, "
                 f"triage: {s['triage_quadrant'].value_counts().sort_index().to_dict()}, "
                 f"feasibility: {s['best_feasibility'].value_counts().sort_index().to_dict()}")

    log.info("=== Expert review tables complete ===")


if __name__ == '__main__':
    main()
