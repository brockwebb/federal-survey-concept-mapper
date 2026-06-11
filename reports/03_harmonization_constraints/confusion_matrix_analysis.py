#!/usr/bin/env python3
"""
Confusion Matrix Analysis + Conservative Arbitration
Report 03: Harmonization Constraints

Analyzes disagreements between OpenAI and Claude barrier coding.
Generates confusion matrix heatmap and applies conservative arbitration.
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict

# Configuration
DATA_DIR = Path("output")
ANALYSIS_DIR = Path("output/analysis")
ANALYSIS_DIR.mkdir(exist_ok=True)

BARRIER_TYPES = ["TC", "CC", "PC", "RS", "MC", "PM"]
FEASIBILITY_LEVELS = ["F1", "F2", "F3"]

def load_results():
    """Load OpenAI and Claude barrier coding results."""
    openai_path = DATA_DIR / "barrier_coding_openai.jsonl"
    claude_path = DATA_DIR / "barrier_coding_claude.jsonl"

    openai_results = {}
    claude_results = {}

    with open(openai_path) as f:
        for line in f:
            data = json.loads(line)
            pair_id = data.get('pair_id')
            openai_results[pair_id] = data

    with open(claude_path) as f:
        for line in f:
            data = json.loads(line)
            pair_id = data.get('pair_id')
            claude_results[pair_id] = data

    return openai_results, claude_results

def extract_barrier_type(barrier_code):
    """Extract Level 1 barrier type from full code (e.g., 'CC.2' -> 'CC')."""
    if not barrier_code or barrier_code == "UNKNOWN":
        return "UNKNOWN"
    return barrier_code.split('.')[0]

def extract_feasibility(feasibility_code):
    """Extract feasibility level."""
    if not feasibility_code:
        return "UNKNOWN"
    return feasibility_code

def analyze_disagreements(openai_results, claude_results):
    """Generate confusion matrices and print disagreement analysis."""

    # Build confusion matrix for Level 1 barriers
    barrier_confusion = defaultdict(lambda: defaultdict(int))
    feasibility_confusion = defaultdict(lambda: defaultdict(int))

    agreements = {
        'level1': 0,
        'full_code': 0,
        'feasibility': 0,
        'total': 0
    }

    disagreement_examples = {
        'level1': [],
        'feasibility': []
    }

    all_pair_ids = set(openai_results.keys()) | set(claude_results.keys())

    for pair_id in all_pair_ids:
        oai_data = openai_results.get(pair_id, {})
        claude_data = claude_results.get(pair_id, {})

        oai_barrier = extract_barrier_type(oai_data.get('barrier_code', 'UNKNOWN'))
        claude_barrier = extract_barrier_type(claude_data.get('barrier_code', 'UNKNOWN'))

        oai_feasibility = extract_feasibility(oai_data.get('feasibility', 'UNKNOWN'))
        claude_feasibility = extract_feasibility(claude_data.get('feasibility', 'UNKNOWN'))

        # Track in confusion matrix
        barrier_confusion[oai_barrier][claude_barrier] += 1
        feasibility_confusion[oai_feasibility][claude_feasibility] += 1

        # Agreement tracking
        agreements['total'] += 1
        if oai_barrier == claude_barrier:
            agreements['level1'] += 1
        else:
            # Store disagreement example
            if len(disagreement_examples['level1']) < 10:
                disagreement_examples['level1'].append({
                    'pair_id': pair_id,
                    'openai': oai_barrier,
                    'claude': claude_barrier,
                    'oai_reasoning': oai_data.get('reasoning', '')[:150],
                    'claude_reasoning': claude_data.get('reasoning', '')[:150]
                })

        if oai_data.get('barrier_code') == claude_data.get('barrier_code'):
            agreements['full_code'] += 1

        if oai_feasibility == claude_feasibility:
            agreements['feasibility'] += 1
        else:
            if len(disagreement_examples['feasibility']) < 10:
                disagreement_examples['feasibility'].append({
                    'pair_id': pair_id,
                    'openai': oai_feasibility,
                    'claude': claude_feasibility
                })

    return barrier_confusion, feasibility_confusion, agreements, disagreement_examples

def generate_heatmap(confusion_matrix, title, filename, cmap='YlOrRd'):
    """Generate and save confusion matrix heatmap."""

    # Convert to DataFrame for visualization
    all_categories = sorted(set(list(confusion_matrix.keys()) +
                                [k for v in confusion_matrix.values() for k in v.keys()]))

    df = pd.DataFrame(0, index=all_categories, columns=all_categories)
    for row_cat in confusion_matrix:
        for col_cat in confusion_matrix[row_cat]:
            df.loc[row_cat, col_cat] = confusion_matrix[row_cat][col_cat]

    plt.figure(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt='d', cmap=cmap, cbar_kws={'label': 'Count'})
    plt.title(title)
    plt.xlabel('Claude Coding')
    plt.ylabel('OpenAI Coding')
    plt.tight_layout()
    plt.savefig(ANALYSIS_DIR / filename, dpi=300)
    plt.close()

    return df

def apply_conservative_arbitration(openai_results, claude_results, barrier_confusion, feasibility_confusion):
    """Apply conservative arbitration rule to disagreements."""

    arbitrated_data = []
    all_pair_ids = sorted(set(openai_results.keys()) | set(claude_results.keys()))

    for pair_id in all_pair_ids:
        oai_data = openai_results.get(pair_id, {})
        claude_data = claude_results.get(pair_id, {})

        oai_barrier = extract_barrier_type(oai_data.get('barrier_code', 'UNKNOWN'))
        claude_barrier = extract_barrier_type(claude_data.get('barrier_code', 'UNKNOWN'))

        # Arbitration rule: use OpenAI if they agree, otherwise default to CC (most common)
        if oai_barrier == claude_barrier:
            final_barrier = oai_barrier
            arbitration_note = "AGREED"
        else:
            final_barrier = "CC"  # Conservative default to most common
            arbitration_note = f"DISAGREED (OAI:{oai_barrier} vs Claude:{claude_barrier}) -> DEFAULT:CC"

        # Same for feasibility
        oai_feasibility = extract_feasibility(oai_data.get('feasibility', 'UNKNOWN'))
        claude_feasibility = extract_feasibility(claude_data.get('feasibility', 'UNKNOWN'))

        if oai_feasibility == claude_feasibility:
            final_feasibility = oai_feasibility
            feas_note = "AGREED"
        else:
            final_feasibility = "F3"  # Conservative default to most common
            feas_note = f"DISAGREED (OAI:{oai_feasibility} vs Claude:{claude_feasibility}) -> DEFAULT:F3"

        # Merge with original pair data
        merged_row = {
            'pair_id': pair_id,
            'final_barrier_type': final_barrier,
            'barrier_arbitration': arbitration_note,
            'final_feasibility': final_feasibility,
            'feasibility_arbitration': feas_note,
            'openai_barrier': oai_barrier,
            'claude_barrier': claude_barrier,
            'openai_feasibility': oai_feasibility,
            'claude_feasibility': claude_feasibility,
            'openai_reasoning': oai_data.get('reasoning', '')[:300],
            'claude_reasoning': claude_data.get('reasoning', '')[:300],
        }

        arbitrated_data.append(merged_row)

    return pd.DataFrame(arbitrated_data)

def print_report(barrier_confusion, feasibility_confusion, agreements, disagreement_examples):
    """Print analysis report to console."""

    print("\n" + "="*70)
    print("CONFUSION MATRIX ANALYSIS")
    print("Report 03: Harmonization Constraints")
    print("="*70)

    print("\n1. AGREEMENT SUMMARY")
    print("-" * 70)
    total = agreements['total']
    print(f"Total pairs: {total}")
    print(f"Level 1 Barrier Agreement: {agreements['level1']}/{total} = {100*agreements['level1']/total:.1f}%")
    print(f"Full Code Agreement: {agreements['full_code']}/{total} = {100*agreements['full_code']/total:.1f}%")
    print(f"Feasibility Agreement: {agreements['feasibility']}/{total} = {100*agreements['feasibility']/total:.1f}%")

    print(f"\nDisagreement rate (Level 1): {total - agreements['level1']}/{total} = {100*(total-agreements['level1'])/total:.1f}%")

    print("\n2. BARRIER CONFUSION PATTERN (Top 5 Disagreements)")
    print("-" * 70)

    disagreement_counts = []
    for oai_cat in barrier_confusion:
        for claude_cat in barrier_confusion[oai_cat]:
            if oai_cat != claude_cat:
                count = barrier_confusion[oai_cat][claude_cat]
                disagreement_counts.append({
                    'openai': oai_cat,
                    'claude': claude_cat,
                    'count': count
                })

    disagreement_counts.sort(key=lambda x: x['count'], reverse=True)
    for item in disagreement_counts[:10]:
        print(f"  {item['openai']} -> {item['claude']}: {item['count']} cases")

    print("\n3. EXAMPLE DISAGREEMENT (Level 1 Barriers)")
    print("-" * 70)
    for i, ex in enumerate(disagreement_examples['level1'][:3]):
        print(f"\nExample {i+1}: {ex['pair_id']}")
        print(f"  OpenAI: {ex['openai']}")
        print(f"  Claude: {ex['claude']}")
        print(f"  OAI reasoning: {ex['oai_reasoning']}")
        print(f"  Claude reasoning: {ex['claude_reasoning']}")

    print("\n4. ARBITRATION RULE")
    print("-" * 70)
    print("Conservative arbitration applied:")
    print("  - On barrier disagreement: default to CC (Construct, most common)")
    print("  - On feasibility disagreement: default to F3 (Incompatible, most common)")
    print("  - When models agree: use agreed value")

    print("\n5. FEASIBILITY CONFUSION PATTERN")
    print("-" * 70)
    feas_disagreement_counts = []
    for oai_cat in feasibility_confusion:
        for claude_cat in feasibility_confusion[oai_cat]:
            if oai_cat != claude_cat:
                count = feasibility_confusion[oai_cat][claude_cat]
                feas_disagreement_counts.append({
                    'openai': oai_cat,
                    'claude': claude_cat,
                    'count': count
                })

    feas_disagreement_counts.sort(key=lambda x: x['count'], reverse=True)
    for item in feas_disagreement_counts[:5]:
        print(f"  {item['openai']} -> {item['claude']}: {item['count']} cases")

    print("\n" + "="*70)

def main():
    print("Loading results...")
    openai_results, claude_results = load_results()

    print("Analyzing disagreements...")
    barrier_confusion, feasibility_confusion, agreements, disagreement_examples = \
        analyze_disagreements(openai_results, claude_results)

    print("Generating heatmaps...")
    barrier_df = generate_heatmap(barrier_confusion,
                                  'Barrier Type Confusion Matrix\n(OpenAI vs Claude)',
                                  'barrier_confusion_matrix.png')

    feasibility_df = generate_heatmap(feasibility_confusion,
                                      'Feasibility Confusion Matrix\n(OpenAI vs Claude)',
                                      'feasibility_confusion_matrix.png',
                                      cmap='Blues')

    print("Applying conservative arbitration...")
    arbitrated_df = apply_conservative_arbitration(openai_results, claude_results,
                                                    barrier_confusion, feasibility_confusion)

    # Save arbitrated results
    arbitrated_df.to_csv(ANALYSIS_DIR / "arbitrated_barriers.csv", index=False)
    print(f"✓ Saved: {ANALYSIS_DIR / 'arbitrated_barriers.csv'}")

    # Print report
    print_report(barrier_confusion, feasibility_confusion, agreements, disagreement_examples)

    print("\n" + "="*70)
    print("OUTPUTS GENERATED:")
    print(f"  ✓ {ANALYSIS_DIR / 'barrier_confusion_matrix.png'}")
    print(f"  ✓ {ANALYSIS_DIR / 'feasibility_confusion_matrix.png'}")
    print(f"  ✓ {ANALYSIS_DIR / 'arbitrated_barriers.csv'}")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
