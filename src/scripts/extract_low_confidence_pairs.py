#!/usr/bin/env python3
"""
Extract LOW confidence pairs with question text for manual review.

Part of Stage 3 arbitration analysis for Report 03.
These 28 pairs have arbitrator disagreement and require expert review.

Usage:
    python extract_low_confidence_pairs.py

Output:
    output/analysis/low_confidence_pairs_detail.csv
"""

import pandas as pd
from pathlib import Path

# Paths
BASE = Path(__file__).parent.parent
OUTPUT_DIR = BASE / "output" / "analysis"
QUESTION_MATCHING_DIR = BASE.parent.parent / "output" / "question_matching"

def main():
    # Load verdicts
    verdicts = pd.read_csv(OUTPUT_DIR / "final_verdicts.csv")
    low = verdicts[verdicts['confidence'] == 'LOW'].copy()
    print(f"LOW confidence pairs: {len(low)}")
    
    # Load question pairs
    cps = pd.read_csv(QUESTION_MATCHING_DIR / "cps" / "cps_candidate_pairs_all.csv")
    food = pd.read_csv(QUESTION_MATCHING_DIR / "foodaps" / "foodaps_candidate_pairs_all.csv")
    pairs = pd.concat([cps, food], ignore_index=True)
    
    # Merge to get question text
    merged = low.merge(
        pairs[['pair_id', 'survey_text', 'acs_text']], 
        on='pair_id', 
        how='left'
    )
    
    # Select columns for output
    cols = [
        'pair_id', 'survey', 'survey_text', 'acs_text', 
        'final_barrier_code', 'final_feasibility',
        'final_barrier_code_oa', 'final_feasibility_oa',
        'final_barrier_code_an', 'final_feasibility_an',
        'final_barrier_code_go', 'final_feasibility_go'
    ]
    
    output_path = OUTPUT_DIR / "low_confidence_pairs_detail.csv"
    merged[cols].to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    
    # Summary stats
    print(f"\nBy survey:")
    print(merged['survey'].value_counts().to_string())
    
    print(f"\nOA vs AN disagreement patterns:")
    merged['disagreement'] = merged['L1_oa'] + ' vs ' + merged['L1_an']
    print(merged['disagreement'].value_counts().head(10).to_string())

if __name__ == "__main__":
    main()
