#!/usr/bin/env python3
"""
Extract compelling example question pairs for presentation slides.

Selects high/medium/low consolidability examples with full text and reasoning.
"""

import pandas as pd
import json
from pathlib import Path

# Paths
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SRC_DIR.parent
sys.path.insert(0, str(SRC_DIR))
BASE = REPO_ROOT  # backward compat alias
BEST_MATCHES = BASE / "output/analysis/stage4_question_best_matches.csv"
ARBITRATION = BASE / "output/analysis/arbitration_merged.csv"
CPS_COMP = BASE / "data/cps_comparison_merged.csv"
FOODAPS_COMP = BASE / "data/foodaps_comparison_merged.csv"

OUTPUT_MD = BASE / "output/analysis/example_pairs_for_presentation.md"
OUTPUT_CSV = BASE / "output/analysis/example_pairs_candidates.csv"

# Selection criteria
HIGH_BORDA_MIN = 0.7
HIGH_ENTROPY_MIN = 0.8
MEDIUM_BORDA_MIN = 0.4
MEDIUM_BORDA_MAX = 0.7
LOW_BORDA_MAX = 0.3

# Keywords to avoid (demographics = expected overlap)
AVOID_KEYWORDS = ['age', 'sex', 'race', 'gender', 'born', 'citizen', 'ancestry', 'ethnic']

# Administrative/metadata keywords (for low consolidability filtering)
ADMIN_KEYWORDS = ['interview', 'respondent', 'replacement', 'household type', 'data quality',
                  'should not be used', 'why do you think', 'reason the information']

def load_data():
    """Load and merge all data sources."""
    print("Loading data...")

    # Best matches
    best = pd.read_csv(BEST_MATCHES)

    # Arbitration results
    arb = pd.read_csv(ARBITRATION)

    # Comparison data (for full question text if needed)
    cps = pd.read_csv(CPS_COMP)
    foodaps = pd.read_csv(FOODAPS_COMP)
    comp = pd.concat([cps, foodaps], ignore_index=True)

    # Merge best matches with arbitration
    # Use pair_id as key
    merged = best.merge(arb[['pair_id',
                             'anthropic_final_barrier_code',
                             'anthropic_reasoning',
                             'openai_final_barrier_code',
                             'openai_reasoning',
                             'google_final_barrier_code',
                             'google_reasoning']],
                       on='pair_id',
                       how='left')

    print(f"Loaded {len(merged)} best-match pairs")
    return merged

def is_demographic(text):
    """Check if question is demographic-related."""
    text_lower = str(text).lower()
    return any(kw in text_lower for kw in AVOID_KEYWORDS)

def is_administrative(text):
    """Check if question is administrative/metadata-related."""
    text_lower = str(text).lower()
    return any(kw in text_lower for kw in ADMIN_KEYWORDS)

def select_high_consolidability(df):
    """Select F1 examples - high Borda, high Entropy, non-demographic."""
    candidates = df[
        (df['best_feasibility'] == 'F1') &
        (df['score_borda'] > HIGH_BORDA_MIN) &
        (df['score_entropy'] > HIGH_ENTROPY_MIN)
    ].copy()

    # Filter out demographics
    candidates = candidates[
        ~candidates['source_text'].apply(is_demographic) &
        ~candidates['best_match_text'].apply(is_demographic)
    ]

    # Sort by Borda score descending
    candidates = candidates.sort_values('score_borda', ascending=False)

    print(f"\nHigh consolidability (F1): {len(candidates)} candidates")
    return candidates.head(10)  # Top 10 for selection

def select_medium_consolidability(df):
    """Select F2 examples - moderate Borda, shows transformation need."""
    candidates = df[
        (df['best_feasibility'] == 'F2') &
        (df['score_borda'] >= MEDIUM_BORDA_MIN) &
        (df['score_borda'] <= MEDIUM_BORDA_MAX)
    ].copy()

    # Filter out demographics
    candidates = candidates[
        ~candidates['source_text'].apply(is_demographic) &
        ~candidates['best_match_text'].apply(is_demographic)
    ]

    # Sort by Borda score descending
    candidates = candidates.sort_values('score_borda', ascending=False)

    print(f"Medium consolidability (F2): {len(candidates)} candidates")
    return candidates.head(10)

def select_low_consolidability(df):
    """Select F3 examples - low Borda, CC barrier preferred."""
    candidates = df[
        (df['best_feasibility'] == 'F3') &
        (df['score_borda'] < LOW_BORDA_MAX)
    ].copy()

    # Prefer CC barrier (construct/concept mismatch)
    candidates['has_cc'] = (
        (candidates['anthropic_final_barrier_code'].str.contains('CC', na=False)) |
        (candidates['openai_final_barrier_code'].str.contains('CC', na=False)) |
        (candidates['google_final_barrier_code'].str.contains('CC', na=False))
    )

    # Filter out demographics and administrative questions
    candidates = candidates[
        ~candidates['source_text'].apply(is_demographic) &
        ~candidates['best_match_text'].apply(is_demographic) &
        ~candidates['source_text'].apply(is_administrative) &
        ~candidates['best_match_text'].apply(is_administrative)
    ]

    # Sort by CC presence, then by Borda ascending
    candidates = candidates.sort_values(['has_cc', 'score_borda'], ascending=[False, True])

    print(f"Low consolidability (F3): {len(candidates)} candidates")
    return candidates.head(10)

def get_best_reasoning(row):
    """Get the most relevant arbitrator reasoning."""
    # Prefer Anthropic reasoning if available
    if pd.notna(row.get('anthropic_reasoning')):
        return row['anthropic_reasoning']
    elif pd.notna(row.get('openai_reasoning')):
        return row['openai_reasoning']
    elif pd.notna(row.get('google_reasoning')):
        return row['google_reasoning']
    else:
        return "No reasoning available"

def get_barrier_code(row):
    """Get the most common barrier code."""
    barriers = []
    if pd.notna(row.get('anthropic_final_barrier_code')):
        barriers.append(row['anthropic_final_barrier_code'])
    if pd.notna(row.get('openai_final_barrier_code')):
        barriers.append(row['openai_final_barrier_code'])
    if pd.notna(row.get('google_final_barrier_code')):
        barriers.append(row['google_final_barrier_code'])

    if barriers:
        # Return most common (or first if tied)
        from collections import Counter
        return Counter(barriers).most_common(1)[0][0]
    return "N/A"

def format_markdown_example(row, category):
    """Format a single example for markdown output."""
    reasoning = get_best_reasoning(row)
    # Truncate reasoning if too long
    if len(reasoning) > 300:
        reasoning = reasoning[:297] + "..."

    barrier_code = get_barrier_code(row) if category == "low" else "N/A"

    md = f"""## {category.upper()} CONSOLIDABILITY: {row['source_q_id']} → {row['best_match_q_id']}

**Source Question ({row['survey']}):**
> {row['source_text']}

**ACS Match:**
> {row['best_match_text']}

**Verdict:** {row['best_feasibility']}
**Barrier Code:** {barrier_code}
**Scores:** Borda = {row['score_borda']:.3f}, Entropy = {row['score_entropy']:.3f}
**Triage:** {row['triage_quadrant']}

**LLM Reasoning:**
> {reasoning}

---

"""
    return md

def generate_markdown(high_df, medium_df, low_df):
    """Generate markdown file with examples."""
    print(f"\nGenerating markdown output: {OUTPUT_MD}")

    with open(OUTPUT_MD, 'w') as f:
        f.write("# Example Question Pairs for Presentation\n\n")
        f.write("**Generated:** 2026-02-02\n")
        f.write("**Purpose:** Slide deck examples showing consolidation spectrum\n\n")
        f.write("---\n\n")

        # High consolidability section
        f.write("# HIGH CONSOLIDABILITY (F1)\n\n")
        f.write("Direct mapping - questions can be consolidated without transformation.\n\n")
        for idx, row in high_df.head(5).iterrows():
            f.write(format_markdown_example(row, "high"))

        # Medium consolidability section
        f.write("\n# MEDIUM CONSOLIDABILITY (F2)\n\n")
        f.write("Consolidable with transformation - questions map with adjustments.\n\n")
        for idx, row in medium_df.head(5).iterrows():
            f.write(format_markdown_example(row, "medium"))

        # Low consolidability section
        f.write("\n# LOW/NO CONSOLIDABILITY (F3)\n\n")
        f.write("Not consolidable - fundamental construct mismatch.\n\n")
        for idx, row in low_df.head(5).iterrows():
            f.write(format_markdown_example(row, "low"))

def generate_csv(high_df, medium_df, low_df):
    """Generate CSV with candidate examples."""
    print(f"Generating CSV output: {OUTPUT_CSV}")

    # Add category labels
    high_df = high_df.copy()
    medium_df = medium_df.copy()
    low_df = low_df.copy()

    high_df['category'] = 'HIGH'
    medium_df['category'] = 'MEDIUM'
    low_df['category'] = 'LOW'

    # Select relevant columns
    cols = ['category', 'survey', 'source_q_id', 'source_text',
            'best_match_q_id', 'best_match_text', 'best_feasibility',
            'score_borda', 'score_entropy', 'triage_quadrant', 'pair_id']

    # Combine and save
    combined = pd.concat([
        high_df[cols].head(5),
        medium_df[cols].head(5),
        low_df[cols].head(5)
    ], ignore_index=True)

    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"Saved {len(combined)} candidate pairs")

def main():
    """Main execution."""
    print("=" * 60)
    print("EXTRACTING EXAMPLE PAIRS FOR PRESENTATION")
    print("=" * 60)

    # Load data
    df = load_data()

    # Select candidates
    high_candidates = select_high_consolidability(df)
    medium_candidates = select_medium_consolidability(df)
    low_candidates = select_low_consolidability(df)

    # Generate outputs
    generate_markdown(high_candidates, medium_candidates, low_candidates)
    generate_csv(high_candidates, medium_candidates, low_candidates)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)
    print(f"\nMarkdown: {OUTPUT_MD}")
    print(f"CSV:      {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
