#!/usr/bin/env python3
"""
Stage 4: Two-Axis Triage Assignment

Assigns pairs to quadrants based on Direction (Borda) × Stability (Entropy).
Uses median splits for threshold determination.

Quadrants:
- Q1: High Direction + High Stability → Auto-accept, verify sample
- Q2: Low Direction + High Stability → Auto-reject, low priority  
- Q3: High Direction + Low Stability → Human review priority (leaning yes but contested)
- Q4: Low Direction + Low Stability → Human review secondary (genuinely ambiguous)

Author: Claude (via CC task)
Date: 2026-01-31
"""

import pandas as pd
import json
from pathlib import Path

# Paths
ANALYSIS_DIR = Path(__file__).parent.parent / "output" / "analysis"
INPUT_FILE = ANALYSIS_DIR / "stage4_bakeoff_scores.csv"
OUTPUT_FILE = ANALYSIS_DIR / "stage4_triage_assignments.csv"
SUMMARY_FILE = ANALYSIS_DIR / "stage4_triage_summary.json"

# Per-quadrant output files
Q1_FILE = ANALYSIS_DIR / "triage_Q1_accept_confident.csv"
Q3_FILE = ANALYSIS_DIR / "triage_Q3_accept_uncertain.csv"
Q4_FILE = ANALYSIS_DIR / "triage_Q4_reject_uncertain.csv"


def assign_quadrant(row, direction_threshold, stability_threshold):
    """Assign pair to quadrant based on thresholds."""
    high_direction = row['score_borda'] >= direction_threshold
    high_stability = row['score_entropy'] >= stability_threshold
    
    if high_direction and high_stability:
        return 'Q1_accept_confident'
    elif not high_direction and high_stability:
        return 'Q2_reject_confident'
    elif high_direction and not high_stability:
        return 'Q3_accept_uncertain'
    else:
        return 'Q4_reject_uncertain'


def main():
    print("=" * 60)
    print("Stage 4: Two-Axis Triage Assignment")
    print("=" * 60)
    
    # Load data
    print(f"\nLoading: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} pairs")
    
    # Compute median thresholds
    direction_threshold = df['score_borda'].median()
    stability_threshold = df['score_entropy'].median()
    
    print(f"\nThresholds (median splits):")
    print(f"  Direction (Borda):  {direction_threshold:.4f}")
    print(f"  Stability (Entropy): {stability_threshold:.4f}")
    
    # Assign quadrants
    df['quadrant'] = df.apply(
        lambda row: assign_quadrant(row, direction_threshold, stability_threshold),
        axis=1
    )
    
    # Summary statistics
    print("\n" + "-" * 40)
    print("Quadrant Distribution:")
    print("-" * 40)
    quadrant_counts = df['quadrant'].value_counts().sort_index()
    for q, count in quadrant_counts.items():
        pct = 100 * count / len(df)
        print(f"  {q}: {count} ({pct:.1f}%)")
    
    # Cross-tab with feasibility
    print("\n" + "-" * 40)
    print("Quadrant × Feasibility Cross-Tab:")
    print("-" * 40)
    crosstab = pd.crosstab(df['quadrant'], df['final_feasibility'])
    print(crosstab.to_string())
    
    # Select output columns
    output_cols = ['pair_id', 'final_feasibility', 'confidence', 
                   'score_borda', 'score_entropy', 'quadrant']
    
    # Save main output
    df[output_cols].to_csv(OUTPUT_FILE, index=False)
    print(f"\nSaved: {OUTPUT_FILE}")
    
    # Save per-quadrant files
    for quadrant, filepath in [('Q1_accept_confident', Q1_FILE),
                                ('Q3_accept_uncertain', Q3_FILE),
                                ('Q4_reject_uncertain', Q4_FILE)]:
        subset = df[df['quadrant'] == quadrant][output_cols]
        subset.to_csv(filepath, index=False)
        print(f"Saved: {filepath} ({len(subset)} pairs)")
    
    # Build summary JSON
    summary = {
        'thresholds': {
            'direction_borda': float(direction_threshold),
            'stability_entropy': float(stability_threshold),
            'method': 'median_split'
        },
        'quadrant_counts': quadrant_counts.to_dict(),
        'total_pairs': len(df),
        'crosstab_quadrant_feasibility': crosstab.to_dict(),
        'interpretation': {
            'Q1_accept_confident': 'High direction + high stability → auto-accept, verify sample',
            'Q2_reject_confident': 'Low direction + high stability → auto-reject, low priority',
            'Q3_accept_uncertain': 'High direction + low stability → HUMAN REVIEW PRIORITY',
            'Q4_reject_uncertain': 'Low direction + low stability → human review secondary'
        },
        'human_review_total': int(
            quadrant_counts.get('Q3_accept_uncertain', 0) + 
            quadrant_counts.get('Q4_reject_uncertain', 0)
        )
    }
    
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"Saved: {SUMMARY_FILE}")
    
    # Final summary
    print("\n" + "=" * 60)
    print("TRIAGE SUMMARY")
    print("=" * 60)
    print(f"Total pairs: {len(df)}")
    print(f"Auto-process (Q1+Q2): {quadrant_counts.get('Q1_accept_confident', 0) + quadrant_counts.get('Q2_reject_confident', 0)}")
    print(f"Human review needed (Q3+Q4): {summary['human_review_total']}")
    print(f"  - Priority (Q3, leaning yes but uncertain): {quadrant_counts.get('Q3_accept_uncertain', 0)}")
    print(f"  - Secondary (Q4, genuinely ambiguous): {quadrant_counts.get('Q4_reject_uncertain', 0)}")
    print("\nDone.")


if __name__ == "__main__":
    main()
