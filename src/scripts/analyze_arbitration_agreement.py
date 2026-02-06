#!/usr/bin/env python3
"""
analyze_arbitration_agreement.py - Inter-arbitrator agreement and bias detection

Part of Report 03: Harmonization Constraints
Stage: 5 - Arbitration Analysis

Input:  output/analysis/arbitration_merged.csv
Output: output/analysis/arbitration_agreement_report.json
        output/analysis/arbitration_agreement_report.md
        output/analysis/position_bias_analysis.csv
        output/analysis/family_bias_analysis.csv

Usage: python analyze_arbitration_agreement.py
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from itertools import combinations
from collections import defaultdict
import sys

# Add lib to path
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.io_utils import load_config


def cohens_kappa_with_details(labels1, labels2):
    """
    Calculate Cohen's Kappa for two raters.
    Returns kappa, observed agreement, expected agreement.
    """
    assert len(labels1) == len(labels2), "Label lists must be same length"

    n = len(labels1)
    if n == 0:
        return None, None, None

    # Get all unique labels
    all_labels = sorted(set(labels1) | set(labels2))
    label_to_idx = {label: i for i, label in enumerate(all_labels)}
    k = len(all_labels)

    # Build confusion matrix
    confusion = np.zeros((k, k), dtype=int)
    for l1, l2 in zip(labels1, labels2):
        confusion[label_to_idx[l1], label_to_idx[l2]] += 1

    # Observed agreement
    p_o = np.trace(confusion) / n

    # Expected agreement (by chance)
    row_sums = confusion.sum(axis=1)
    col_sums = confusion.sum(axis=0)
    p_e = np.sum(row_sums * col_sums) / (n * n)

    # Kappa
    if p_e == 1.0:
        kappa = 1.0 if p_o == 1.0 else 0.0
    else:
        kappa = (p_o - p_e) / (1 - p_e)

    return kappa, p_o, p_e


def fleiss_kappa_with_details(ratings_matrix):
    """
    Calculate Fleiss' Kappa for multiple raters.
    ratings_matrix: DataFrame where rows are subjects, columns are categories,
                    values are counts of raters who assigned that category.
    """
    n_subjects = len(ratings_matrix)
    n_raters = ratings_matrix.iloc[0].sum()  # Assume constant across subjects
    n_categories = len(ratings_matrix.columns)

    if n_subjects == 0 or n_raters < 2:
        return None, None, None

    # P_i for each subject (proportion of agreeing pairs)
    P_i = []
    for idx, row in ratings_matrix.iterrows():
        n_ij_squared_sum = (row ** 2).sum()
        p_i = (n_ij_squared_sum - n_raters) / (n_raters * (n_raters - 1))
        P_i.append(p_i)

    P_bar = np.mean(P_i)  # Observed agreement

    # p_j for each category (proportion of all assignments)
    p_j = ratings_matrix.sum() / (n_subjects * n_raters)
    P_e_bar = (p_j ** 2).sum()  # Expected agreement

    # Fleiss' Kappa
    if P_e_bar == 1.0:
        kappa = 1.0 if P_bar == 1.0 else 0.0
    else:
        kappa = (P_bar - P_e_bar) / (1 - P_e_bar)

    return kappa, P_bar, P_e_bar


def extract_l1_barrier(barrier_code):
    """Extract Level 1 barrier from full code (e.g., 'TMP.1' -> 'TMP')"""
    if pd.isna(barrier_code) or barrier_code is None:
        return None
    return str(barrier_code).split('.')[0]


def build_ratings_matrix_for_fleiss(df, arbitrators, column_suffix):
    """
    Build ratings matrix for Fleiss' kappa.
    Each row is a pair_id, each column is a category, values are counts.
    """
    # Collect all ratings per pair
    pair_ratings = defaultdict(list)

    for arb in arbitrators:
        col = f"{arb}_{column_suffix}"
        if col not in df.columns:
            continue
        for idx, row in df.iterrows():
            val = row[col]
            if pd.notna(val):
                pair_ratings[row['pair_id']].append(val)

    # Filter to pairs with all raters
    n_raters = len(arbitrators)
    complete_pairs = {k: v for k, v in pair_ratings.items() if len(v) == n_raters}

    if not complete_pairs:
        return None

    # Get all categories
    all_categories = sorted(set(cat for ratings in complete_pairs.values() for cat in ratings))

    # Build matrix
    matrix_data = []
    for pair_id, ratings in complete_pairs.items():
        row = {cat: 0 for cat in all_categories}
        for r in ratings:
            row[r] += 1
        matrix_data.append(row)

    return pd.DataFrame(matrix_data)


def analyze_position_bias(df, arbitrators):
    """
    Analyze whether rater position affects selection probability.
    Returns bias statistics per arbitrator.
    """
    results = []

    for arb in arbitrators:
        selected_col = f"{arb}_selected_rater"
        order_col = f"{arb}_rater_order"
        order_type_col = f"{arb}_order_type"

        if selected_col not in df.columns:
            continue

        # Filter to non-synthesis cases (actual selections)
        arb_data = df[df[selected_col].notna() & (df[selected_col] != 'synthesis')].copy()

        if len(arb_data) == 0:
            continue

        # Parse rater order if available
        if order_col in df.columns:
            # Count position of selected rater
            position_counts = {'first': 0, 'second': 0, 'third': 0, 'unknown': 0}

            for idx, row in arb_data.iterrows():
                selected = row[selected_col]
                order = row[order_col]

                if pd.isna(order):
                    position_counts['unknown'] += 1
                    continue

                # Parse order (format varies - handle common cases)
                try:
                    if isinstance(order, str):
                        order_list = [x.strip() for x in order.split(',')]
                    elif isinstance(order, list):
                        order_list = order
                    else:
                        position_counts['unknown'] += 1
                        continue

                    if selected in order_list:
                        pos = order_list.index(selected)
                        if pos == 0:
                            position_counts['first'] += 1
                        elif pos == 1:
                            position_counts['second'] += 1
                        elif pos == 2:
                            position_counts['third'] += 1
                    else:
                        position_counts['unknown'] += 1
                except:
                    position_counts['unknown'] += 1

            total_known = sum(v for k, v in position_counts.items() if k != 'unknown')

            results.append({
                'arbitrator': arb,
                'total_selections': len(arb_data),
                'first_position': position_counts['first'],
                'second_position': position_counts['second'],
                'third_position': position_counts['third'],
                'unknown_position': position_counts['unknown'],
                'first_pct': position_counts['first'] / total_known * 100 if total_known > 0 else None,
                'expected_pct': 33.33
            })
        else:
            # No order info - just count selections by rater key
            selection_counts = arb_data[selected_col].value_counts().to_dict()
            results.append({
                'arbitrator': arb,
                'total_selections': len(arb_data),
                'selection_distribution': selection_counts
            })

    return pd.DataFrame(results)


def analyze_family_bias(df, arbitrators, config):
    """
    Analyze whether arbitrators prefer raters from same vendor family.
    """
    # Map rater keys to families
    rater_families = {}
    for rater_key, rater_config in config.get('raters', {}).items():
        rater_families[rater_key] = rater_key  # rater_key is the family (anthropic, openai, google)

    results = []

    for arb in arbitrators:
        arb_family = arb  # arbitrator key is the family
        selected_col = f"{arb}_selected_rater"

        if selected_col not in df.columns:
            continue

        # Filter to non-synthesis cases
        arb_data = df[df[selected_col].notna() & (df[selected_col] != 'synthesis')].copy()

        if len(arb_data) == 0:
            continue

        # Count same-family vs cross-family selections
        same_family = 0
        cross_family = 0

        for idx, row in arb_data.iterrows():
            selected = row[selected_col]

            # Extract family from selected rater key (format: "rater_X" or just the key)
            selected_family = None
            for rater_key in rater_families:
                if rater_key in str(selected).lower():
                    selected_family = rater_families[rater_key]
                    break

            if selected_family is None:
                # Try direct match
                selected_family = selected.lower() if isinstance(selected, str) else None

            if selected_family == arb_family:
                same_family += 1
            else:
                cross_family += 1

        total = same_family + cross_family
        expected_same_pct = 33.33  # With 3 raters, 1/3 chance of same family

        results.append({
            'arbitrator': arb,
            'arbitrator_family': arb_family,
            'total_selections': total,
            'same_family_selections': same_family,
            'cross_family_selections': cross_family,
            'same_family_pct': same_family / total * 100 if total > 0 else None,
            'expected_same_pct': expected_same_pct,
            'bias_ratio': (same_family / total * 100) / expected_same_pct if total > 0 else None
        })

    return pd.DataFrame(results)


def analyze_synthesis_rate(df, arbitrators):
    """
    Analyze how often all 3 raters agreed (synthesis = no arbitration needed).
    """
    results = []

    for arb in arbitrators:
        selected_col = f"{arb}_selected_rater"

        if selected_col not in df.columns:
            continue

        arb_data = df[df[selected_col].notna()].copy()

        if len(arb_data) == 0:
            continue

        synthesis_count = (arb_data[selected_col] == 'synthesis').sum()
        total = len(arb_data)

        results.append({
            'arbitrator': arb,
            'total_pairs': total,
            'synthesis_count': synthesis_count,
            'arbitration_needed': total - synthesis_count,
            'synthesis_pct': synthesis_count / total * 100 if total > 0 else None
        })

    return pd.DataFrame(results)


def generate_markdown_report(report_data, output_path):
    """Generate human-readable markdown report."""
    lines = [
        "# Arbitration Agreement Analysis Report",
        "",
        f"**Generated:** {report_data['timestamp']}",
        f"**Total pairs analyzed:** {report_data['total_pairs']}",
        "",
        "---",
        "",
        "## 1. Inter-Arbitrator Agreement",
        "",
        "### Pairwise Agreement (Cohen's Kappa)",
        "",
        "| Pair | N | Level | Kappa | Observed | Expected | Interpretation |",
        "|------|---|-------|-------|----------|----------|----------------|"
    ]

    def interpret_kappa(k):
        if k is None:
            return "N/A"
        if k < 0:
            return "Poor"
        if k < 0.20:
            return "Slight"
        if k < 0.40:
            return "Fair"
        if k < 0.60:
            return "Moderate"
        if k < 0.80:
            return "Substantial"
        return "Almost Perfect"

    for pair_result in report_data.get('pairwise_agreement', []):
        pair = pair_result['pair']
        n = pair_result['n']
        for level, stats in pair_result.get('levels', {}).items():
            kappa = stats.get('kappa')
            obs = stats.get('observed_agreement')
            exp = stats.get('expected_agreement')
            kappa_str = f"{kappa:.3f}" if kappa is not None else "N/A"
            obs_str = f"{obs:.1%}" if obs is not None else "N/A"
            exp_str = f"{exp:.1%}" if exp is not None else "N/A"
            interp = interpret_kappa(kappa)
            lines.append(f"| {pair} | {n} | {level} | {kappa_str} | {obs_str} | {exp_str} | {interp} |")

    lines.extend([
        "",
        "### Three-Way Agreement (Fleiss' Kappa)",
        "",
        "| Level | N | Kappa | Observed | Expected | Interpretation |",
        "|-------|---|-------|----------|----------|----------------|"
    ])

    for level, stats in report_data.get('three_way_agreement', {}).items():
        n = stats.get('n', 0)
        kappa = stats.get('kappa')
        obs = stats.get('observed_agreement')
        exp = stats.get('expected_agreement')
        kappa_str = f"{kappa:.3f}" if kappa is not None else "N/A"
        obs_str = f"{obs:.1%}" if obs is not None else "N/A"
        exp_str = f"{exp:.1%}" if exp is not None else "N/A"
        interp = interpret_kappa(kappa)
        lines.append(f"| {level} | {n} | {kappa_str} | {obs_str} | {exp_str} | {interp} |")

    lines.extend([
        "",
        "---",
        "",
        "## 2. Synthesis Rate (Unanimous Agreement)",
        "",
        "When all 3 raters agree, arbitrators return `synthesis` - no selection needed.",
        "",
        "| Arbitrator | Total Pairs | Synthesis | Arbitration Needed | Synthesis % |",
        "|------------|-------------|-----------|-------------------|-------------|"
    ])

    for row in report_data.get('synthesis_rates', []):
        arb = row['arbitrator']
        total = row['total_pairs']
        synth = row['synthesis_count']
        needed = row['arbitration_needed']
        pct = row['synthesis_pct']
        pct_str = f"{pct:.1f}%" if pct is not None else "N/A"
        lines.append(f"| {arb} | {total} | {synth} | {needed} | {pct_str} |")

    lines.extend([
        "",
        "---",
        "",
        "## 3. Family Bias Analysis",
        "",
        "Do arbitrators prefer raters from their own vendor family?",
        "",
        "| Arbitrator | Total | Same Family | Cross Family | Same % | Expected % | Bias Ratio |",
        "|------------|-------|-------------|--------------|--------|------------|------------|"
    ])

    for row in report_data.get('family_bias', []):
        arb = row['arbitrator']
        total = row['total_selections']
        same = row['same_family_selections']
        cross = row['cross_family_selections']
        same_pct = row['same_family_pct']
        exp_pct = row['expected_same_pct']
        ratio = row['bias_ratio']
        same_str = f"{same_pct:.1f}%" if same_pct is not None else "N/A"
        ratio_str = f"{ratio:.2f}" if ratio is not None else "N/A"
        lines.append(f"| {arb} | {total} | {same} | {cross} | {same_str} | {exp_pct:.1f}% | {ratio_str} |")

    lines.extend([
        "",
        "*Bias ratio > 1.0 indicates preference for same-family raters.*",
        "",
        "---",
        "",
        "## 4. Coverage Notes",
        "",
        f"- **Two-way analysis:** {report_data.get('two_way_n', 0)} pairs (Anthropic + OpenAI)",
        f"- **Three-way analysis:** {report_data.get('three_way_n', 0)} pairs (all 3 arbitrators)",
        f"- **Google limitation:** Rate-limited, only CPS pairs covered",
        ""
    ])

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))


def main():
    # Setup paths
    base_dir = REPO_ROOT  # post-restructure: use repo root
    analysis_dir = base_dir / "output" / "report_03" / "analysis"

    # Load config and data
    config = load_config(base_dir / "config" / "report_03.yaml")
    merged_file = analysis_dir / "arbitration_merged.csv"

    print(f"Loading {merged_file.name}...")
    df = pd.read_csv(merged_file)
    print(f"  Loaded {len(df)} pairs")

    # Arbitrator list
    arbitrators = list(config.get('arbitrators', {}).keys())
    print(f"  Arbitrators: {arbitrators}")

    # Initialize report
    report = {
        'timestamp': datetime.now().isoformat(),
        'total_pairs': len(df),
        'arbitrators': arbitrators
    }

    # --- 1. Inter-Arbitrator Agreement ---
    print("\n1. Computing inter-arbitrator agreement...")

    # Add L1 barrier columns
    for arb in arbitrators:
        col = f"{arb}_final_barrier_code"
        if col in df.columns:
            df[f"{arb}_l1_barrier"] = df[col].apply(extract_l1_barrier)

    # Pairwise agreement
    pairwise_results = []
    for arb1, arb2 in combinations(arbitrators, 2):
        col1_l1 = f"{arb1}_l1_barrier"
        col2_l1 = f"{arb2}_l1_barrier"
        col1_full = f"{arb1}_final_barrier_code"
        col2_full = f"{arb2}_final_barrier_code"
        col1_feas = f"{arb1}_final_feasibility"
        col2_feas = f"{arb2}_final_feasibility"

        # Filter to pairs where both have data
        mask = df[col1_full].notna() & df[col2_full].notna()
        subset = df[mask]
        n = len(subset)

        if n == 0:
            continue

        pair_name = f"{arb1}-{arb2}"
        print(f"  {pair_name}: n={n}")

        levels = {}

        # L1 barrier
        if col1_l1 in df.columns and col2_l1 in df.columns:
            kappa, obs, exp = cohens_kappa_with_details(subset[col1_l1].tolist(), subset[col2_l1].tolist())
            levels['L1_barrier'] = {'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
            print(f"    L1 barrier: \u03ba={kappa:.3f}" if kappa else "    L1 barrier: N/A")

        # Full barrier code
        kappa, obs, exp = cohens_kappa_with_details(subset[col1_full].tolist(), subset[col2_full].tolist())
        levels['full_barrier'] = {'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
        print(f"    Full barrier: \u03ba={kappa:.3f}" if kappa else "    Full barrier: N/A")

        # Feasibility
        if col1_feas in df.columns and col2_feas in df.columns:
            feas_mask = subset[col1_feas].notna() & subset[col2_feas].notna()
            feas_subset = subset[feas_mask]
            if len(feas_subset) > 0:
                kappa, obs, exp = cohens_kappa_with_details(feas_subset[col1_feas].tolist(), feas_subset[col2_feas].tolist())
                levels['feasibility'] = {'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
                print(f"    Feasibility: \u03ba={kappa:.3f}" if kappa else "    Feasibility: N/A")

        pairwise_results.append({
            'pair': pair_name,
            'n': n,
            'levels': levels
        })

    report['pairwise_agreement'] = pairwise_results
    report['two_way_n'] = max((r['n'] for r in pairwise_results), default=0)

    # Three-way agreement (Fleiss' kappa)
    print("\n  Three-way agreement...")
    three_way = {}

    # Filter to pairs with all 3 arbitrators
    coverage_col = 'coverage'
    if coverage_col in df.columns:
        three_way_mask = df['coverage_count'] == 3
        three_way_df = df[three_way_mask]
        n_three = len(three_way_df)
        print(f"    Pairs with all 3 arbitrators: {n_three}")
        report['three_way_n'] = n_three

        if n_three > 0:
            # L1 barrier
            matrix = build_ratings_matrix_for_fleiss(three_way_df, arbitrators, 'l1_barrier')
            if matrix is not None:
                kappa, obs, exp = fleiss_kappa_with_details(matrix)
                three_way['L1_barrier'] = {'n': n_three, 'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
                print(f"    L1 barrier: Fleiss' \u03ba={kappa:.3f}" if kappa else "    L1 barrier: N/A")

            # Full barrier
            matrix = build_ratings_matrix_for_fleiss(three_way_df, arbitrators, 'final_barrier_code')
            if matrix is not None:
                kappa, obs, exp = fleiss_kappa_with_details(matrix)
                three_way['full_barrier'] = {'n': n_three, 'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
                print(f"    Full barrier: Fleiss' \u03ba={kappa:.3f}" if kappa else "    Full barrier: N/A")

            # Feasibility
            matrix = build_ratings_matrix_for_fleiss(three_way_df, arbitrators, 'final_feasibility')
            if matrix is not None:
                kappa, obs, exp = fleiss_kappa_with_details(matrix)
                three_way['feasibility'] = {'n': n_three, 'kappa': kappa, 'observed_agreement': obs, 'expected_agreement': exp}
                print(f"    Feasibility: Fleiss' \u03ba={kappa:.3f}" if kappa else "    Feasibility: N/A")

    report['three_way_agreement'] = three_way

    # --- 2. Synthesis Rate ---
    print("\n2. Computing synthesis rates...")
    synthesis_df = analyze_synthesis_rate(df, arbitrators)
    report['synthesis_rates'] = synthesis_df.to_dict('records')
    for _, row in synthesis_df.iterrows():
        pct = row['synthesis_pct']
        print(f"  {row['arbitrator']}: {row['synthesis_count']}/{row['total_pairs']} ({pct:.1f}%)" if pct else f"  {row['arbitrator']}: N/A")

    # --- 3. Family Bias ---
    print("\n3. Analyzing family bias...")
    family_df = analyze_family_bias(df, arbitrators, config)
    report['family_bias'] = family_df.to_dict('records')
    family_df.to_csv(analysis_dir / "family_bias_analysis.csv", index=False)
    print(f"  Written: family_bias_analysis.csv")

    for _, row in family_df.iterrows():
        ratio = row['bias_ratio']
        print(f"  {row['arbitrator']}: same-family={row['same_family_pct']:.1f}%, ratio={ratio:.2f}" if ratio else f"  {row['arbitrator']}: N/A")

    # --- 4. Position Bias ---
    print("\n4. Analyzing position bias...")
    position_df = analyze_position_bias(df, arbitrators)
    report['position_bias'] = position_df.to_dict('records')
    position_df.to_csv(analysis_dir / "position_bias_analysis.csv", index=False)
    print(f"  Written: position_bias_analysis.csv")

    # --- Write Reports ---
    print("\nWriting reports...")

    # JSON report
    json_path = analysis_dir / "arbitration_agreement_report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"  Written: {json_path.name}")

    # Markdown report
    md_path = analysis_dir / "arbitration_agreement_report.md"
    generate_markdown_report(report, md_path)
    print(f"  Written: {md_path.name}")

    print("\nDone.")


if __name__ == "__main__":
    main()
