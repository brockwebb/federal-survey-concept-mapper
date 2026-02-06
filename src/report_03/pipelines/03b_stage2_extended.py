#!/usr/bin/env python3
"""
Stage 2 Extended Analytics

Extends stage2_agreement_metrics.json with:
1. Binary consolidability agreement (F1+F2 vs F3)
2. Conditional barrier agreement & disagreement patterns
3. Multi-model value quantification
4. Light reasoning analysis

Per cc_tasks/CLAUDE_CODE_TASK_stage2_extended_analytics.md
"""
import json
import re
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

from scripts.lib.io_utils import ensure_dir
from scripts.lib.taxonomy import extract_l1
from scripts.lib.stats import (
    cohens_kappa,
    fleiss_kappa,
    percent_agreement,
    krippendorff_alpha,
    interpret_kappa_mchugh
)


RATERS = ['openai', 'anthropic', 'google']
PAIRS = [('openai', 'anthropic'), ('openai', 'google'), ('anthropic', 'google')]
ABBREV = {'openai': 'OA', 'anthropic': 'AN', 'google': 'GO'}


def load_and_prepare(base_dir):
    """Load CSV and existing JSON artifact."""
    input_path = base_dir / 'output/analysis/barrier_coding_merged_3rater.csv'
    json_path = base_dir / 'output/analysis/stage2_agreement_metrics.json'

    df = pd.read_csv(input_path)

    # Extract L1 columns
    for r in RATERS:
        df[f'L1_{r}'] = df[f'primary_barrier_{r}'].apply(extract_l1)
        df[f'L2_{r}'] = df[f'primary_barrier_{r}']

    df['survey'] = df['pair_id'].str.split('_').str[0]

    with open(json_path) as f:
        artifact = json.load(f)

    return df, artifact


# ---------------------------------------------------------------------------
# Task 1: Binary Consolidability
# ---------------------------------------------------------------------------

def compute_binary_consolidability(df):
    """Collapse F1+F2 -> Consolidable, F3 -> Not_Consolidable."""
    result = {"binary_feasibility": {}}

    for rater in RATERS:
        df[f'consolidable_{rater}'] = df[f'feasibility_{rater}'].apply(
            lambda x: 'Consolidable' if x in ['F1', 'F2'] else 'Not_Consolidable'
        )

    labels = {r: df[f'consolidable_{r}'].values for r in RATERS}
    ratings_matrix = np.column_stack([labels[r] for r in RATERS])

    # Pairwise
    pairwise = {}
    for r1, r2 in PAIRS:
        pair_key = f"{ABBREV[r1]}_vs_{ABBREV[r2]}"
        pct = percent_agreement(labels[r1], labels[r2])
        kappa = cohens_kappa(labels[r1], labels[r2])
        interp, passed = interpret_kappa_mchugh(kappa)

        pairwise[pair_key] = {
            "percent_agreement": round(float(pct * 100), 1),
            "cohens_kappa": round(float(kappa), 3),
            "interpretation": interp,
            "quality_gate_passed": passed
        }

    result["binary_feasibility"]["pairwise"] = pairwise

    # Three-way
    fleiss = fleiss_kappa(ratings_matrix)
    alpha = krippendorff_alpha(ratings_matrix)
    interp, passed = interpret_kappa_mchugh(fleiss)

    result["binary_feasibility"]["three_way"] = {
        "fleiss_kappa": round(float(fleiss), 3),
        "krippendorff_alpha": round(float(alpha), 3),
        "interpretation": interp,
        "quality_gate_passed": passed
    }

    # Distribution
    result["binary_feasibility"]["distribution"] = {
        "consolidable_count": int((df['consolidable_openai'] == 'Consolidable').sum()),
        "not_consolidable_count": int((df['consolidable_openai'] == 'Not_Consolidable').sum()),
        "note": "Counts based on OpenAI as reference rater"
    }

    return result


# ---------------------------------------------------------------------------
# Task 2a: F3 Barrier Agreement
# ---------------------------------------------------------------------------

def compute_f3_barrier_agreement(df):
    """Among unanimous F3 cases, do raters agree on the barrier type?"""
    f3_mask = (
        (df['feasibility_openai'] == 'F3') &
        (df['feasibility_anthropic'] == 'F3') &
        (df['feasibility_google'] == 'F3')
    )
    df_f3 = df[f3_mask].copy()

    result = {
        "unanimous_f3": {
            "n_pairs": len(df_f3),
            "pct_of_total": round(len(df_f3) / len(df) * 100, 1)
        }
    }

    if len(df_f3) >= 30:
        labels = {r: df_f3[f'L1_{r}'].astype(str).values for r in RATERS}
        ratings_matrix = np.column_stack([labels[r] for r in RATERS])

        # Pairwise
        pairwise = {}
        for r1, r2 in PAIRS:
            pair_key = f"{ABBREV[r1]}_vs_{ABBREV[r2]}"
            pct = percent_agreement(labels[r1], labels[r2])
            kappa = cohens_kappa(labels[r1], labels[r2])
            interp, passed = interpret_kappa_mchugh(kappa)
            pairwise[pair_key] = {
                "percent_agreement": round(float(pct * 100), 1),
                "cohens_kappa": round(float(kappa), 3),
                "interpretation": interp
            }

        fleiss = fleiss_kappa(ratings_matrix)
        alpha = krippendorff_alpha(ratings_matrix)

        result["unanimous_f3"]["L1_agreement"] = {
            "n_pairs": len(df_f3),
            "pairwise": pairwise,
            "three_way": {
                "fleiss_kappa": round(float(fleiss), 3),
                "krippendorff_alpha": round(float(alpha), 3),
                "interpretation": interpret_kappa_mchugh(fleiss)[0]
            }
        }

        l1_counts = df_f3['L1_openai'].value_counts().to_dict()
        result["unanimous_f3"]["L1_distribution"] = {k: int(v) for k, v in l1_counts.items()}

    return result


# ---------------------------------------------------------------------------
# Task 2b: Disagreement Patterns
# ---------------------------------------------------------------------------

def compute_disagreement_patterns(df):
    """Characterize disagreement cases and arbitration workload."""
    results = {}

    feas_cols = [f'feasibility_{r}' for r in RATERS]
    l1_cols = [f'L1_{r}' for r in RATERS]

    df['feas_unanimous'] = df.apply(
        lambda row: len(set(row[c] for c in feas_cols)) == 1, axis=1
    )
    df['l1_unanimous'] = df.apply(
        lambda row: len(set(row[c] for c in l1_cols)) == 1, axis=1
    )

    results["feasibility_disagreements"] = {
        "unanimous_count": int(df['feas_unanimous'].sum()),
        "disagreement_count": int((~df['feas_unanimous']).sum()),
        "disagreement_pct": round((~df['feas_unanimous']).mean() * 100, 1)
    }

    results["L1_disagreements"] = {
        "unanimous_count": int(df['l1_unanimous'].sum()),
        "disagreement_count": int((~df['l1_unanimous']).sum()),
        "disagreement_pct": round((~df['l1_unanimous']).mean() * 100, 1)
    }

    # Cross-tabulate
    both_agree = df['feas_unanimous'] & df['l1_unanimous']
    l1_only = (~df['l1_unanimous']) & df['feas_unanimous']
    feas_only = (~df['feas_unanimous']) & df['l1_unanimous']
    both_disagree = (~df['feas_unanimous']) & (~df['l1_unanimous'])

    results["disagreement_crosstab"] = {
        "both_agree": int(both_agree.sum()),
        "l1_disagree_only": int(l1_only.sum()),
        "feasibility_disagree_only": int(feas_only.sum()),
        "both_disagree": int(both_disagree.sum())
    }

    needs_arbitration = ~(df['feas_unanimous'] & df['l1_unanimous'])
    results["arbitration_workload"] = {
        "pairs_needing_arbitration": int(needs_arbitration.sum()),
        "pct_needing_arbitration": round(needs_arbitration.mean() * 100, 1)
    }

    return results


# ---------------------------------------------------------------------------
# Task 2c: Pairwise Disagreement Detail
# ---------------------------------------------------------------------------

def compute_pairwise_disagreement_detail(df):
    """For each rater pair, what specific disagreements occur?"""
    results = {}

    for r1, r2 in PAIRS:
        pair_key = f"{ABBREV[r1]}_vs_{ABBREV[r2]}"

        # L1 disagreements
        l1_disagree = df[df[f'L1_{r1}'] != df[f'L1_{r2}']]
        transition_list = []
        if len(l1_disagree) > 0:
            transitions = l1_disagree.groupby([f'L1_{r1}', f'L1_{r2}']).size()
            transitions = transitions.sort_values(ascending=False).head(10)
            transition_list = [
                {"from": idx[0], "to": idx[1], "count": int(v)}
                for idx, v in transitions.items()
            ]

        # Feasibility disagreements
        feas_disagree = df[df[f'feasibility_{r1}'] != df[f'feasibility_{r2}']]
        feas_transitions = []
        if len(feas_disagree) > 0:
            ft = feas_disagree.groupby([f'feasibility_{r1}', f'feasibility_{r2}']).size()
            ft = ft.sort_values(ascending=False)
            feas_transitions = [
                {"from": idx[0], "to": idx[1], "count": int(v)}
                for idx, v in ft.items()
            ]

        results[pair_key] = {
            "L1_disagreements": len(l1_disagree),
            "L1_top_transitions": transition_list,
            "feasibility_disagreements": len(feas_disagree),
            "feasibility_transitions": feas_transitions
        }

    return results


# ---------------------------------------------------------------------------
# Task 3: Multi-Model Value
# ---------------------------------------------------------------------------

def compute_multimodel_value(df):
    """Quantify the value of using multiple models vs single model."""
    results = {}

    l1_cols = [f'L1_{r}' for r in RATERS]
    feas_cols = [f'feasibility_{r}' for r in RATERS]

    def vote_pattern(row, cols):
        votes = [row[c] for c in cols]
        unique = len(set(votes))
        if unique == 1:
            return "unanimous"
        elif unique == 2:
            return "2-1_split"
        else:
            return "3-way_split"

    df['l1_vote_pattern'] = df.apply(lambda r: vote_pattern(r, l1_cols), axis=1)
    df['feas_vote_pattern'] = df.apply(lambda r: vote_pattern(r, feas_cols), axis=1)

    results["L1_vote_patterns"] = {k: int(v) for k, v in df['l1_vote_pattern'].value_counts().items()}
    results["feasibility_vote_patterns"] = {k: int(v) for k, v in df['feas_vote_pattern'].value_counts().items()}

    # Majority vote
    def majority_vote(row, cols):
        votes = [row[c] for c in cols]
        return max(set(votes), key=votes.count)

    df['l1_majority'] = df.apply(lambda r: majority_vote(r, l1_cols), axis=1)
    df['feas_majority'] = df.apply(lambda r: majority_vote(r, feas_cols), axis=1)

    single_model_risk = {}
    for rater in RATERS:
        l1_match = (df[f'L1_{rater}'] == df['l1_majority']).mean()
        feas_match = (df[f'feasibility_{rater}'] == df['feas_majority']).mean()
        single_model_risk[rater] = {
            "L1_matches_majority_pct": round(float(l1_match * 100), 1),
            "feasibility_matches_majority_pct": round(float(feas_match * 100), 1),
            "L1_diverges_from_majority": int((df[f'L1_{rater}'] != df['l1_majority']).sum()),
            "feas_diverges_from_majority": int((df[f'feasibility_{rater}'] != df['feas_majority']).sum())
        }

    results["single_model_risk"] = single_model_risk

    results["multimodel_value_summary"] = {
        "pairs_where_models_disagree_L1": int((df['l1_vote_pattern'] != 'unanimous').sum()),
        "pairs_where_models_disagree_feas": int((df['feas_vote_pattern'] != 'unanimous').sum()),
        "note": "These cases justify multi-model + arbitration approach"
    }

    return results


# ---------------------------------------------------------------------------
# Task 4: Light Reasoning Analysis
# ---------------------------------------------------------------------------

def analyze_disagreement_reasoning(df):
    """Keyword frequency in reasoning text for disagreement cases."""
    l1_cols = [f'L1_{r}' for r in RATERS]
    df['l1_unanimous'] = df.apply(
        lambda row: len(set(row[c] for c in l1_cols)) == 1, axis=1
    )
    disagree_df = df[~df['l1_unanimous']]

    if len(disagree_df) == 0:
        return {"note": "No disagreements to analyze"}

    reasoning_texts = []
    for rater in RATERS:
        col = f'reasoning_{rater}'
        if col in disagree_df.columns:
            reasoning_texts.extend(disagree_df[col].dropna().tolist())

    keywords = [
        'temporal', 'time', 'period', 'reference',
        'construct', 'concept', 'definition', 'meaning',
        'response', 'scale', 'format', 'categorical', 'numeric',
        'population', 'coverage', 'universe', 'subset',
        'mode', 'context', 'interview', 'self-report',
        'harmoniz', 'consolidat', 'compatibl', 'reconcil'
    ]

    all_text = ' '.join(str(t) for t in reasoning_texts).lower()
    keyword_counts = {}
    for kw in keywords:
        keyword_counts[kw] = len(re.findall(kw, all_text))

    keyword_counts = dict(sorted(keyword_counts.items(), key=lambda x: -x[1]))

    return {
        "n_disagreement_cases": len(disagree_df),
        "total_reasoning_texts_analyzed": len(reasoning_texts),
        "keyword_frequencies": keyword_counts
    }


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_extended_report(artifact, output_path):
    """Generate markdown report for extended analytics."""
    ext = artifact.get('extended_analytics', {})
    lines = []

    lines.append("# Stage 2 Extended Analytics Report")
    lines.append("")
    lines.append(f"**Generated:** {artifact['metadata'].get('extended_generated_at', 'N/A')}")
    lines.append(f"**Total Pairs:** {artifact['metadata']['total_pairs']:,}")
    lines.append("")

    # Binary Consolidability
    bc = ext.get('binary_consolidability', {}).get('binary_feasibility', {})
    if bc:
        lines.append("## Binary Consolidability (F1+F2 vs F3)")
        lines.append("")
        dist = bc.get('distribution', {})
        lines.append(f"- Consolidable (F1+F2): {dist.get('consolidable_count', '?'):,}")
        lines.append(f"- Not Consolidable (F3): {dist.get('not_consolidable_count', '?'):,}")
        lines.append("")

        tw = bc.get('three_way', {})
        lines.append(f"- **Fleiss' kappa:** {tw.get('fleiss_kappa', '?'):.3f} ({tw.get('interpretation', '?')})")
        lines.append(f"- **Krippendorff's alpha:** {tw.get('krippendorff_alpha', '?'):.3f}")
        lines.append(f"- **Quality Gate:** {'PASSED' if tw.get('quality_gate_passed') else 'NOT PASSED'}")
        lines.append("")

        lines.append("### Pairwise")
        lines.append("")
        lines.append("| Comparison | % Agreement | Cohen's kappa | Interpretation |")
        lines.append("|------------|-------------|---------------|----------------|")
        for pair, data in bc.get('pairwise', {}).items():
            lines.append(f"| {pair.replace('_', ' ')} | {data['percent_agreement']:.1f}% | {data['cohens_kappa']:.3f} | {data['interpretation']} |")
        lines.append("")

    # Disagreement Patterns
    cond = ext.get('conditional_agreement', {})
    dp = cond.get('disagreement_patterns', {})
    if dp:
        lines.append("## Disagreement Patterns")
        lines.append("")
        l1d = dp.get('L1_disagreements', {})
        fd = dp.get('feasibility_disagreements', {})
        lines.append(f"- **L1 unanimous:** {l1d.get('unanimous_count', '?'):,} ({100 - l1d.get('disagreement_pct', 0):.1f}%)")
        lines.append(f"- **L1 disagreements:** {l1d.get('disagreement_count', '?'):,} ({l1d.get('disagreement_pct', '?')}%)")
        lines.append(f"- **Feasibility unanimous:** {fd.get('unanimous_count', '?'):,} ({100 - fd.get('disagreement_pct', 0):.1f}%)")
        lines.append(f"- **Feasibility disagreements:** {fd.get('disagreement_count', '?'):,} ({fd.get('disagreement_pct', '?')}%)")
        lines.append("")

        ct = dp.get('disagreement_crosstab', {})
        lines.append("### Disagreement Cross-Tabulation")
        lines.append("")
        lines.append("| | L1 Agree | L1 Disagree |")
        lines.append("|---|---|---|")
        lines.append(f"| **Feas Agree** | {ct.get('both_agree', '?'):,} | {ct.get('l1_disagree_only', '?'):,} |")
        lines.append(f"| **Feas Disagree** | {ct.get('feasibility_disagree_only', '?'):,} | {ct.get('both_disagree', '?'):,} |")
        lines.append("")

        aw = dp.get('arbitration_workload', {})
        lines.append(f"**Arbitration workload:** {aw.get('pairs_needing_arbitration', '?'):,} pairs ({aw.get('pct_needing_arbitration', '?')}%)")
        lines.append("")

    # Unanimous F3
    uf3 = cond.get('unanimous_f3', {}).get('unanimous_f3', {})
    if uf3:
        lines.append("## Unanimous F3 Barrier Agreement")
        lines.append("")
        lines.append(f"- **n:** {uf3.get('n_pairs', '?'):,} ({uf3.get('pct_of_total', '?')}% of total)")
        l1a = uf3.get('L1_agreement', {}).get('three_way', {})
        if l1a:
            lines.append(f"- **L1 Fleiss' kappa:** {l1a.get('fleiss_kappa', '?'):.3f} ({l1a.get('interpretation', '?')})")
        l1d = uf3.get('L1_distribution', {})
        if l1d:
            lines.append("")
            lines.append("### L1 Distribution (within unanimous F3)")
            lines.append("")
            lines.append("| Category | Count |")
            lines.append("|----------|-------|")
            for cat in sorted(l1d.keys(), key=lambda c: -l1d[c]):
                lines.append(f"| {cat} | {l1d[cat]:,} |")
        lines.append("")

    # Multi-Model Value
    mmv = ext.get('multimodel_value', {})
    if mmv:
        lines.append("## Multi-Model Value")
        lines.append("")
        vp = mmv.get('L1_vote_patterns', {})
        lines.append("### Vote Patterns (L1)")
        lines.append("")
        for pattern in ['unanimous', '2-1_split', '3-way_split']:
            count = vp.get(pattern, 0)
            pct = round(count / artifact['metadata']['total_pairs'] * 100, 1)
            lines.append(f"- **{pattern}:** {count:,} ({pct}%)")
        lines.append("")

        lines.append("### Single-Model Risk")
        lines.append("")
        lines.append("| Model | L1 matches majority | Feasibility matches majority |")
        lines.append("|-------|---------------------|------------------------------|")
        for rater, data in mmv.get('single_model_risk', {}).items():
            lines.append(f"| {rater} | {data['L1_matches_majority_pct']:.1f}% | {data['feasibility_matches_majority_pct']:.1f}% |")
        lines.append("")

        summ = mmv.get('multimodel_value_summary', {})
        lines.append(f"**L1 disagreements:** {summ.get('pairs_where_models_disagree_L1', '?'):,} pairs")
        lines.append(f"**Feasibility disagreements:** {summ.get('pairs_where_models_disagree_feas', '?'):,} pairs")
        lines.append("")

    # Reasoning Analysis
    ra = ext.get('reasoning_analysis', {})
    if ra and 'keyword_frequencies' in ra:
        lines.append("## Reasoning Keyword Analysis (Disagreement Cases)")
        lines.append("")
        lines.append(f"- Cases analyzed: {ra.get('n_disagreement_cases', '?'):,}")
        lines.append(f"- Reasoning texts: {ra.get('total_reasoning_texts_analyzed', '?'):,}")
        lines.append("")
        lines.append("| Keyword | Frequency |")
        lines.append("|---------|-----------|")
        for kw, count in list(ra['keyword_frequencies'].items())[:15]:
            lines.append(f"| {kw} | {count:,} |")
        lines.append("")

    lines.append("---")
    lines.append("*Report generated from `stage2_agreement_metrics.json` extended_analytics section*")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Saved extended report: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base_dir = Path(__file__).parent

    print("Loading data...")
    df, artifact = load_and_prepare(base_dir)
    print(f"  Loaded {len(df)} pairs")

    extended = {}

    print("Computing binary consolidability...")
    extended["binary_consolidability"] = compute_binary_consolidability(df)

    print("Computing conditional agreement (unanimous F3)...")
    f3_result = compute_f3_barrier_agreement(df)

    print("Computing disagreement patterns...")
    disagreement_result = compute_disagreement_patterns(df)

    print("Computing pairwise disagreement detail...")
    pairwise_detail = compute_pairwise_disagreement_detail(df)

    extended["conditional_agreement"] = {
        "unanimous_f3": f3_result,
        "disagreement_patterns": disagreement_result,
        "pairwise_disagreement_detail": pairwise_detail
    }

    print("Computing multi-model value...")
    extended["multimodel_value"] = compute_multimodel_value(df)

    print("Analyzing disagreement reasoning...")
    extended["reasoning_analysis"] = analyze_disagreement_reasoning(df)

    # Merge into artifact
    artifact["extended_analytics"] = extended
    artifact["metadata"]["extended_generated_at"] = datetime.now().isoformat()

    # Save updated JSON
    json_path = base_dir / 'output/analysis/stage2_agreement_metrics.json'
    with open(json_path, 'w') as f:
        json.dump(artifact, f, indent=2)
    print(f"Saved updated JSON: {json_path}")

    # Generate extended report
    report_path = base_dir / 'output/analysis/stage2_extended_report.md'
    generate_extended_report(artifact, report_path)

    print("Done!")


if __name__ == '__main__':
    main()
