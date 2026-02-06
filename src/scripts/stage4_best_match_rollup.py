#!/usr/bin/env python3
"""
stage4_best_match_rollup.py - Identify best consolidable ACS match per source question

Joins pair-level bake-off scores with question mappings to produce one row per
source question with its best ACS match, scores, and triage quadrant assignment.

Usage:
    python scripts/stage4_best_match_rollup.py
"""

import sys
import logging
from pathlib import Path

import pandas as pd

# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.io_utils import ensure_dir, load_merged_csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / "output" / "report_03" / "analysis"


def main():
    log.info("=== Stage 4: Best-Match Rollup ===")

    # --- Load data ---
    scores = pd.read_csv(OUTPUT_DIR / "stage4_bakeoff_scores.csv")
    questions = pd.read_csv(OUTPUT_DIR / "stage4_question_level.csv")
    verdicts = pd.read_csv(OUTPUT_DIR / "final_verdicts.csv")[['pair_id', 'survey']]

    cps_map = load_merged_csv(REPO_ROOT / "data" / "processed" / "cps_comparison_merged.csv")
    foodaps_map = load_merged_csv(REPO_ROOT / "data" / "processed" / "foodaps_comparison_merged.csv")

    map_cols = ['pair_id', 'survey_q_id', 'survey_text', 'acs_q_id', 'acs_text']
    question_map = pd.concat([cps_map[map_cols], foodaps_map[map_cols]], ignore_index=True)

    log.info(f"Loaded: {len(scores)} scores, {len(questions)} questions, {len(question_map)} mappings")

    # --- Join scores with survey + question mapping ---
    pairs = scores.merge(verdicts, on='pair_id', how='left')
    pairs = pairs.merge(question_map, on='pair_id', how='left')

    unmatched = pairs['survey_q_id'].isna().sum()
    if unmatched > 0:
        log.warning(f"{unmatched} pairs have no question mapping")

    # --- Find best match per source question ---
    # Priority: F1 > F2 > F3, then highest Borda score
    pairs['feasibility_rank'] = pairs['final_feasibility'].map({'F1': 3, 'F2': 2, 'F3': 1})
    pairs = pairs.sort_values(['feasibility_rank', 'score_borda'], ascending=[False, False])

    best = pairs.groupby(['survey', 'survey_q_id']).first().reset_index()
    log.info(f"Best matches: {len(best)} questions")

    # --- Triage quadrant assignment ---
    # Use median thresholds from the best-match scores (not pair-level, where
    # most pairs are F3 with Borda=0, making the pair-level median degenerate)
    borda_thresh = best['score_borda'].median()
    entropy_thresh = best['score_entropy'].median()
    log.info(f"Triage thresholds — Borda: {borda_thresh:.3f}, Entropy: {entropy_thresh:.3f}")

    def assign_quadrant(row):
        high_borda = row['score_borda'] >= borda_thresh
        high_entropy = row['score_entropy'] >= entropy_thresh
        if high_borda and high_entropy:
            return 'Q1'   # Confident consolidable
        elif not high_borda and high_entropy:
            return 'Q2'   # Confident non-consolidable
        elif high_borda and not high_entropy:
            return 'Q3'   # Edge case — leaning yes but contested
        else:
            return 'Q4'   # Ambiguous

    best['triage_quadrant'] = best.apply(assign_quadrant, axis=1)

    # --- Add has_consolidable_path from question-level ---
    best = best.merge(
        questions[['survey', 'survey_q_id', 'has_consolidable_path']],
        on=['survey', 'survey_q_id'],
        how='left'
    )

    # --- Truncate text columns ---
    max_text = 120
    best['source_text'] = best['survey_text'].fillna('').str[:max_text]
    best['best_match_text'] = best['acs_text'].fillna('').str[:max_text]

    # --- Select output columns ---
    output = best[[
        'survey', 'survey_q_id', 'source_text', 'has_consolidable_path',
        'acs_q_id', 'best_match_text', 'final_feasibility',
        'score_borda', 'score_entropy', 'triage_quadrant', 'pair_id'
    ]].rename(columns={
        'survey_q_id': 'source_q_id',
        'acs_q_id': 'best_match_q_id',
        'final_feasibility': 'best_feasibility',
    })

    output = output.sort_values(['survey', 'source_q_id'])

    # --- Validation ---
    errors = []

    if len(output) != len(questions):
        errors.append(f"Row count mismatch: {len(output)} vs {len(questions)} questions")

    consolidable = output[output['has_consolidable_path'] == True]
    bad_consol = consolidable[~consolidable['best_feasibility'].isin(['F1', 'F2'])]
    if len(bad_consol) > 0:
        errors.append(f"{len(bad_consol)} consolidable questions have best_feasibility != F1/F2")

    not_consolidable = output[output['has_consolidable_path'] == False]
    bad_f3 = not_consolidable[not_consolidable['best_feasibility'] != 'F3']
    if len(bad_f3) > 0:
        errors.append(f"{len(bad_f3)} non-consolidable questions have best_feasibility != F3")

    null_matches = output['best_match_q_id'].isna().sum()
    if null_matches > 0:
        errors.append(f"{null_matches} questions have null best_match_q_id")

    quad_counts = output['triage_quadrant'].value_counts()
    if len(quad_counts) < 2:
        errors.append(f"Only {len(quad_counts)} quadrant(s) populated: {quad_counts.to_dict()}")

    if errors:
        for e in errors:
            log.error(f"Validation error: {e}")
        raise ValueError(f"{len(errors)} validation errors")

    log.info("All validation checks passed")

    # --- Save ---
    out_path = OUTPUT_DIR / "stage4_question_best_matches.csv"
    output.to_csv(out_path, index=False)
    log.info(f"Wrote {out_path}")

    # --- Summary ---
    log.info(f"Total questions: {len(output)}")
    log.info(f"With consolidable path: {output['has_consolidable_path'].sum()}")
    log.info(f"By triage quadrant:\n{quad_counts.to_string()}")
    log.info(f"By best feasibility:\n{output['best_feasibility'].value_counts().to_string()}")

    # Per-survey breakdown
    for survey in sorted(output['survey'].unique()):
        s = output[output['survey'] == survey]
        log.info(f"{survey}: {len(s)} questions, "
                 f"{s['has_consolidable_path'].sum()} consolidable, "
                 f"quadrants: {s['triage_quadrant'].value_counts().to_dict()}")

    log.info("=== Best-match rollup complete ===")


if __name__ == '__main__':
    main()
