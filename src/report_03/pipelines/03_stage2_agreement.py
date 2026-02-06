#!/usr/bin/env python3
"""
Stage 2: Inter-Rater Agreement Analysis

Computes agreement metrics for three LLM raters on barrier classification.
Outputs JSON artifact and human-readable report.

Per SPEC-R03-S2-001
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

# Local imports
from scripts.lib.io_utils import load_config, ensure_dir
from scripts.lib.taxonomy import extract_l1, BARRIER_L1, FEASIBILITY_LEVELS
from scripts.lib.stats import (
    cohens_kappa,
    fleiss_kappa,
    percent_agreement,
    krippendorff_alpha,
    interpret_kappa_mchugh
)


def load_and_prepare_data(input_path):
    """Load merged 3-rater CSV and extract L1/L2/feasibility columns."""
    df = pd.read_csv(input_path)

    # Extract L1 from L1.L2 format
    df['L1_openai'] = df['primary_barrier_openai'].apply(extract_l1)
    df['L1_anthropic'] = df['primary_barrier_anthropic'].apply(extract_l1)
    df['L1_google'] = df['primary_barrier_google'].apply(extract_l1)

    # L2 is the full code (already in L1.L2 format)
    df['L2_openai'] = df['primary_barrier_openai']
    df['L2_anthropic'] = df['primary_barrier_anthropic']
    df['L2_google'] = df['primary_barrier_google']

    # Extract survey from pair_id
    df['survey'] = df['pair_id'].str.split('_').str[0]

    return df


def compute_power_verification(df):
    """
    Compute statistical power verification per spec Section 6.

    Thresholds:
    - ADEQUATE: n >= 200
    - MARGINAL: 50 <= n < 200
    - UNDERPOWERED: n < 50
    """
    n_required = 200  # For k=7 categories, alpha=0.80, p=0.05

    def status(n):
        if n >= 200:
            return "ADEQUATE"
        elif n >= 50:
            return "MARGINAL"
        else:
            return "UNDERPOWERED"

    result = {
        "overall": {
            "n_observed": len(df),
            "n_required_k7_alpha80_p05": n_required,
            "ratio": round(len(df) / n_required, 2),
            "status": status(len(df))
        },
        "by_stratum": {},
        "by_category": {},
        "methodology_note": "Per Krippendorff (2004) via ATLAS.ti guidance. Categories with n<50 flagged as underpowered for independent reliability estimation."
    }

    # By survey
    for survey in ['CPS', 'FOODAPS']:
        n = len(df[df['survey'] == survey])
        result["by_stratum"][survey] = {
            "n": n,
            "n_required": n_required,
            "status": status(n)
        }

    # By L1 category (using OpenAI as reference)
    l1_counts = df['L1_openai'].value_counts()
    for cat in ['CC', 'TC', 'RS', 'PC', 'MC', 'PM', 'NHB']:
        n = l1_counts.get(cat, 0)
        result["by_category"][cat] = {
            "n": int(n),
            "status": status(n)
        }

    # Combined "Other" category
    other_n = sum(l1_counts.get(c, 0) for c in ['PC', 'MC', 'PM', 'NHB'])
    result["by_category"]["Other_combined"] = {
        "n": int(other_n),
        "status": status(other_n),
        "components": ["PC", "MC", "PM", "NHB"]
    }

    return result


def compute_agreement_metrics(df, level_col_prefix, raters=None):
    """
    Compute all agreement metrics for a given classification level.

    Args:
        df: DataFrame with columns {level_col_prefix}_{rater}
        level_col_prefix: 'L1', 'L2', or 'feasibility'
        raters: list of rater identifiers

    Returns:
        dict with all metrics
    """
    if raters is None:
        raters = ['openai', 'anthropic', 'google']

    # Prepare data
    labels = {r: df[f'{level_col_prefix}_{r}'].astype(str).values for r in raters}

    # Ratings matrix for multi-rater metrics (n_items, n_raters)
    ratings_matrix = np.column_stack([labels[r] for r in raters])

    result = {
        "n_pairs": len(df),
        "pairwise": {},
        "three_way": {}
    }

    # Pairwise metrics
    pairs = [('openai', 'anthropic'), ('openai', 'google'), ('anthropic', 'google')]
    abbrev = {'openai': 'OA', 'anthropic': 'AN', 'google': 'GO'}

    for r1, r2 in pairs:
        pair_key = f"{abbrev[r1]}_vs_{abbrev[r2]}"
        pct = percent_agreement(labels[r1], labels[r2])
        kappa = cohens_kappa(labels[r1], labels[r2])
        interp, passed = interpret_kappa_mchugh(kappa)

        result["pairwise"][pair_key] = {
            "percent_agreement": round(float(pct * 100), 1),
            "cohens_kappa": round(float(kappa), 3),
            "interpretation": interp,
            "quality_gate_passed": passed
        }

    # Three-way metrics
    fleiss = fleiss_kappa(ratings_matrix)
    alpha = krippendorff_alpha(ratings_matrix, level_of_measurement='nominal')

    fleiss_interp, fleiss_passed = interpret_kappa_mchugh(fleiss)
    alpha_interp, alpha_passed = interpret_kappa_mchugh(alpha)

    result["three_way"] = {
        "fleiss_kappa": round(float(fleiss), 3),
        "fleiss_interpretation": fleiss_interp,
        "fleiss_quality_gate_passed": fleiss_passed,
        "krippendorff_alpha": round(float(alpha), 3),
        "krippendorff_interpretation": alpha_interp,
        "krippendorff_quality_gate_passed": alpha_passed
    }

    return result


def compute_stratified_metrics(df, level_col_prefix):
    """Compute metrics stratified by survey and by L1 category."""
    result = {
        "by_survey": {},
        "by_L1_category": {}
    }

    # By survey
    for survey in df['survey'].unique():
        subset = df[df['survey'] == survey]
        result["by_survey"][survey] = compute_agreement_metrics(
            subset, level_col_prefix
        )

    # By L1 category (only for L1 and L2 levels, not feasibility)
    # Only compute for categories with sufficient sample size
    if level_col_prefix in ['L1', 'L2']:
        for cat in ['CC', 'TC', 'RS']:  # Individual categories
            subset = df[df['L1_openai'] == cat]
            if len(subset) >= 30:  # Minimum for any statistics
                result["by_L1_category"][cat] = compute_agreement_metrics(
                    subset, level_col_prefix
                )

        # Combined "Other"
        other_cats = ['PC', 'MC', 'PM', 'NHB']
        subset = df[df['L1_openai'].isin(other_cats)]
        if len(subset) >= 30:
            result["by_L1_category"]["Other_combined"] = compute_agreement_metrics(
                subset, level_col_prefix
            )

    return result


def compute_confusion_matrices(df, level_col_prefix, output_dir):
    """
    Generate confusion matrices for each pairwise comparison.
    Save as CSV and return summary statistics.
    """
    from sklearn.metrics import confusion_matrix as sklearn_cm

    pairs = [('openai', 'anthropic'), ('openai', 'google'), ('anthropic', 'google')]
    abbrev = {'openai': 'OA', 'anthropic': 'AN', 'google': 'GO'}

    results = {}

    for r1, r2 in pairs:
        pair_key = f"{abbrev[r1]}_{abbrev[r2]}"

        labels1 = df[f'{level_col_prefix}_{r1}'].astype(str).values
        labels2 = df[f'{level_col_prefix}_{r2}'].astype(str).values

        # Get all unique labels
        all_labels = sorted(list(set(labels1) | set(labels2)))

        # Compute confusion matrix
        cm = sklearn_cm(labels1, labels2, labels=all_labels)

        # Save as CSV
        cm_df = pd.DataFrame(cm, index=all_labels, columns=all_labels)
        cm_path = output_dir / f"confusion_matrix_{level_col_prefix}_{pair_key}.csv"
        cm_df.to_csv(cm_path)

        # Find top confusion pairs (off-diagonal)
        confusions = []
        for i, l1 in enumerate(all_labels):
            for j, l2 in enumerate(all_labels):
                if i != j and cm[i, j] > 0:
                    confusions.append({
                        "from": l1,
                        "to": l2,
                        "count": int(cm[i, j])
                    })
        confusions.sort(key=lambda x: x['count'], reverse=True)

        results[pair_key] = {
            "file": str(cm_path.name),
            "diagonal_sum": int(np.trace(cm)),
            "off_diagonal_sum": int(cm.sum() - np.trace(cm)),
            "top_confusions": confusions[:5]
        }

    return results


def generate_report(artifact, output_path):
    """Generate human-readable markdown report from JSON artifact."""
    lines = []

    lines.append("# Stage 2: Inter-Rater Agreement Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {artifact['metadata']['generated_at']}")
    lines.append(f"**Input:** {artifact['metadata']['input_file']}")
    lines.append(f"**Total Pairs:** {artifact['metadata']['total_pairs']:,}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    l1_overall = artifact['L1_agreement']['overall']['three_way']
    lines.append(f"- **L1 Fleiss' kappa:** {l1_overall['fleiss_kappa']:.3f} ({l1_overall['fleiss_interpretation']})")
    lines.append(f"- **L1 Krippendorff's alpha:** {l1_overall['krippendorff_alpha']:.3f} ({l1_overall['krippendorff_interpretation']})")
    lines.append(f"- **Quality Gate (kappa/alpha >= 0.80):** {'PASSED' if l1_overall['krippendorff_quality_gate_passed'] else 'NOT PASSED'}")
    lines.append("")

    # Statistical Validity
    lines.append("## Statistical Validity")
    lines.append("")
    pv = artifact['power_verification']
    lines.append(f"**Overall:** n={pv['overall']['n_observed']:,} (required: {pv['overall']['n_required_k7_alpha80_p05']}) -- **{pv['overall']['status']}**")
    lines.append("")
    lines.append("### By Survey")
    lines.append("")
    lines.append("| Survey | n | Status |")
    lines.append("|--------|---|--------|")
    for survey, data in pv['by_stratum'].items():
        lines.append(f"| {survey} | {data['n']:,} | {data['status']} |")
    lines.append("")

    lines.append("### By L1 Category")
    lines.append("")
    lines.append("| Category | n | Status |")
    lines.append("|----------|---|--------|")
    for cat, data in pv['by_category'].items():
        lines.append(f"| {cat} | {data['n']:,} | {data['status']} |")
    lines.append("")
    lines.append(f"*{pv['methodology_note']}*")
    lines.append("")

    # L1 Agreement Results
    lines.append("## L1 Agreement Results")
    lines.append("")
    lines.append("### Pairwise Metrics")
    lines.append("")
    lines.append("| Comparison | % Agreement | Cohen's kappa | Interpretation |")
    lines.append("|------------|-------------|---------------|----------------|")
    for pair, data in artifact['L1_agreement']['overall']['pairwise'].items():
        lines.append(f"| {pair.replace('_', ' ')} | {data['percent_agreement']:.1f}% | {data['cohens_kappa']:.3f} | {data['interpretation']} |")
    lines.append("")

    lines.append("### Three-Way Metrics")
    lines.append("")
    tw = artifact['L1_agreement']['overall']['three_way']
    lines.append(f"- **Fleiss' kappa:** {tw['fleiss_kappa']:.3f} ({tw['fleiss_interpretation']})")
    lines.append(f"- **Krippendorff's alpha:** {tw['krippendorff_alpha']:.3f} ({tw['krippendorff_interpretation']})")
    lines.append("")

    # L1 Stratified by survey
    if 'stratified' in artifact['L1_agreement'] and 'by_survey' in artifact['L1_agreement']['stratified']:
        lines.append("### L1 by Survey")
        lines.append("")
        lines.append("| Survey | n | Fleiss' kappa | Krippendorff's alpha |")
        lines.append("|--------|---|---------------|----------------------|")
        for survey, data in artifact['L1_agreement']['stratified']['by_survey'].items():
            tw_s = data['three_way']
            lines.append(f"| {survey} | {data['n_pairs']:,} | {tw_s['fleiss_kappa']:.3f} | {tw_s['krippendorff_alpha']:.3f} |")
        lines.append("")

    # L1 Stratified by category
    if 'stratified' in artifact['L1_agreement'] and 'by_L1_category' in artifact['L1_agreement']['stratified']:
        by_cat = artifact['L1_agreement']['stratified']['by_L1_category']
        if by_cat:
            lines.append("### L1 by Dominant Category")
            lines.append("")
            lines.append("| Category | n | Fleiss' kappa | Krippendorff's alpha |")
            lines.append("|----------|---|---------------|----------------------|")
            for cat, data in by_cat.items():
                tw_c = data['three_way']
                lines.append(f"| {cat} | {data['n_pairs']:,} | {tw_c['fleiss_kappa']:.3f} | {tw_c['krippendorff_alpha']:.3f} |")
            lines.append("")

    # L2 Agreement Results
    lines.append("## L2 Agreement Results")
    lines.append("")
    lines.append("### Pairwise Metrics")
    lines.append("")
    lines.append("| Comparison | % Agreement | Cohen's kappa | Interpretation |")
    lines.append("|------------|-------------|---------------|----------------|")
    for pair, data in artifact['L2_agreement']['overall']['pairwise'].items():
        lines.append(f"| {pair.replace('_', ' ')} | {data['percent_agreement']:.1f}% | {data['cohens_kappa']:.3f} | {data['interpretation']} |")
    lines.append("")

    l2_tw = artifact['L2_agreement']['overall']['three_way']
    lines.append("### Three-Way Metrics")
    lines.append("")
    lines.append(f"- **Fleiss' kappa:** {l2_tw['fleiss_kappa']:.3f} ({l2_tw['fleiss_interpretation']})")
    lines.append(f"- **Krippendorff's alpha:** {l2_tw['krippendorff_alpha']:.3f} ({l2_tw['krippendorff_interpretation']})")
    lines.append("")

    # Feasibility Agreement Results
    lines.append("## Feasibility Agreement Results")
    lines.append("")
    lines.append("### Pairwise Metrics")
    lines.append("")
    lines.append("| Comparison | % Agreement | Cohen's kappa | Interpretation |")
    lines.append("|------------|-------------|---------------|----------------|")
    for pair, data in artifact['feasibility_agreement']['overall']['pairwise'].items():
        lines.append(f"| {pair.replace('_', ' ')} | {data['percent_agreement']:.1f}% | {data['cohens_kappa']:.3f} | {data['interpretation']} |")
    lines.append("")

    f_tw = artifact['feasibility_agreement']['overall']['three_way']
    lines.append("### Three-Way Metrics")
    lines.append("")
    lines.append(f"- **Fleiss' kappa:** {f_tw['fleiss_kappa']:.3f} ({f_tw['fleiss_interpretation']})")
    lines.append(f"- **Krippendorff's alpha:** {f_tw['krippendorff_alpha']:.3f} ({f_tw['krippendorff_interpretation']})")
    lines.append("")

    # Top Confusions
    lines.append("## Disagreement Analysis")
    lines.append("")
    lines.append("### L1 Top Confusions")
    lines.append("")
    for pair, data in artifact['confusion_matrices']['L1'].items():
        lines.append(f"**{pair.replace('_', ' ')}:** {data['diagonal_sum']:,} agreements, {data['off_diagonal_sum']:,} disagreements")
        if data['top_confusions']:
            top3 = data['top_confusions'][:3]
            confusion_str = ", ".join([f"{c['from']}->{c['to']} ({c['count']})" for c in top3])
            lines.append(f"  - Top confusions: {confusion_str}")
        lines.append("")

    # Methodology
    lines.append("## Methodology")
    lines.append("")
    lines.append("Metrics computed per McHugh (2012) and Krippendorff (2004) guidelines:")
    lines.append("- **Cohen's kappa:** Pairwise chance-corrected agreement")
    lines.append("- **Fleiss' kappa:** Multi-rater extension of Cohen's kappa")
    lines.append("- **Krippendorff's alpha:** Robust to prevalence imbalance and missing data")
    lines.append("")
    lines.append("**Quality Gate Threshold:** kappa/alpha >= 0.80 (McHugh 2012: \"Almost Perfect\" for health research)")
    lines.append("")
    lines.append("---")
    lines.append(f"*Report generated from `stage2_agreement_metrics.json`*")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Saved report: {output_path}")


def main():
    """Main execution."""
    # Setup paths
    base_dir = Path(__file__).parent
    input_path = base_dir / 'output/analysis/barrier_coding_merged_3rater.csv'
    output_dir = base_dir / 'output/analysis'
    confusion_dir = output_dir / 'confusion_matrices'

    ensure_dir(confusion_dir)

    print("Loading data...")
    df = load_and_prepare_data(input_path)
    print(f"  Loaded {len(df)} pairs")

    # Build JSON artifact
    artifact = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "input_file": str(input_path.name),
            "total_pairs": len(df),
            "spec_version": "SPEC-R03-S2-001 v1.0"
        },
        "power_verification": compute_power_verification(df),
        "L1_agreement": {},
        "L2_agreement": {},
        "feasibility_agreement": {},
        "confusion_matrices": {}
    }

    print("Computing L1 agreement metrics...")
    artifact["L1_agreement"]["overall"] = compute_agreement_metrics(df, 'L1')
    artifact["L1_agreement"]["stratified"] = compute_stratified_metrics(df, 'L1')
    artifact["confusion_matrices"]["L1"] = compute_confusion_matrices(df, 'L1', confusion_dir)

    print("Computing L2 agreement metrics...")
    artifact["L2_agreement"]["overall"] = compute_agreement_metrics(df, 'L2')
    artifact["L2_agreement"]["stratified"] = compute_stratified_metrics(df, 'L2')
    artifact["confusion_matrices"]["L2"] = compute_confusion_matrices(df, 'L2', confusion_dir)

    print("Computing feasibility agreement metrics...")
    artifact["feasibility_agreement"]["overall"] = compute_agreement_metrics(df, 'feasibility')
    artifact["feasibility_agreement"]["stratified"] = compute_stratified_metrics(df, 'feasibility')
    artifact["confusion_matrices"]["feasibility"] = compute_confusion_matrices(df, 'feasibility', confusion_dir)

    # Save JSON artifact
    json_path = output_dir / 'stage2_agreement_metrics.json'
    with open(json_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    print(f"Saved JSON artifact: {json_path}")

    # Generate report from JSON
    print("Generating report...")
    generate_report(artifact, output_dir / 'stage2_agreement_report.md')

    print("Done!")


if __name__ == '__main__':
    main()
