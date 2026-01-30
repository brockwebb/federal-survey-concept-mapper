#!/usr/bin/env python3
"""
Arbitrator Comparison Analysis v2.0
Report 03: Harmonization Constraints

Compares arbitration results across different arbitrator models:
- Agreement rates between arbitrators
- Source preference (model_a vs model_b vs synthesis)
- Decision patterns by barrier type
- Cost/performance tradeoffs

Usage:
    Called from run_pipeline.py, not directly.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from collections import Counter


# =============================================================================
# COMPARISON METRICS
# =============================================================================

def calculate_agreement(df1: pd.DataFrame, df2: pd.DataFrame,
                       col: str, id_col: str = 'pair_id') -> Dict:
    """Calculate agreement between two arbitrator outputs."""

    # Merge on pair_id
    merged = df1[[id_col, col]].merge(
        df2[[id_col, col]],
        on=id_col,
        suffixes=('_1', '_2')
    )

    if len(merged) == 0:
        return {'agreement': 0.0, 'n_common': 0}

    col1 = f'{col}_1'
    col2 = f'{col}_2'

    # Calculate agreement
    agree = (merged[col1] == merged[col2]).sum()
    total = len(merged)

    return {
        'agreement': agree / total if total > 0 else 0.0,
        'n_common': total,
        'n_agree': agree,
        'n_disagree': total - agree
    }


def analyze_source_preferences(df: pd.DataFrame, arb_name: str) -> Dict:
    """Analyze which rater the arbitrator tends to agree with."""

    if 'arbitration_source' not in df.columns:
        return {}

    source_counts = df['arbitration_source'].value_counts().to_dict()
    total = len(df)

    return {
        'arbitrator': arb_name,
        'total_arbitrated': total,
        'source_distribution': {
            k: {'count': v, 'pct': v/total*100}
            for k, v in source_counts.items()
        }
    }


def analyze_barrier_patterns(df: pd.DataFrame, arb_name: str) -> Dict:
    """Analyze arbitration patterns by barrier type."""

    if 'arbitrated_barrier' not in df.columns:
        return {}

    # Extract L1 codes
    df = df.copy()
    df['barrier_L1'] = df['arbitrated_barrier'].apply(
        lambda x: str(x).split('.')[0] if pd.notna(x) else 'UNKNOWN'
    )

    # Count by L1
    barrier_counts = df['barrier_L1'].value_counts().to_dict()

    # Source by barrier type
    source_by_barrier = {}
    if 'arbitration_source' in df.columns:
        for barrier in df['barrier_L1'].unique():
            mask = df['barrier_L1'] == barrier
            sources = df.loc[mask, 'arbitration_source'].value_counts().to_dict()
            source_by_barrier[barrier] = sources

    return {
        'arbitrator': arb_name,
        'barrier_distribution': barrier_counts,
        'source_by_barrier': source_by_barrier
    }


# =============================================================================
# MAIN COMPARISON FUNCTION
# =============================================================================

def run_arbitrator_comparison(config: Dict) -> Dict:
    """Run comparison analysis across arbitrators.

    Args:
        config: Pipeline configuration dictionary

    Returns:
        Dictionary of comparison results
    """

    output_dir = Path(config['paths']['output_dir'])
    analysis_dir = output_dir / config['paths']['analysis_subdir']
    results_dir = output_dir / config['paths']['results_subdir']

    print("\n" + "="*50)
    print("ARBITRATOR COMPARISON ANALYSIS")
    print("="*50)

    # Find all arbitration result files
    arbitrator_data = {}

    for arb_key, arb_config in config['arbitrators'].items():
        model = arb_config['model']
        model_safe = model.replace('/', '-').replace(':', '-')

        # Check for results file
        results_path = results_dir / f'arbitration_results_{arb_key}_{model_safe}.jsonl'

        if not results_path.exists():
            print(f"\nSkipping {arb_key}: no results found at {results_path}")
            continue

        # Load results
        records = []
        with open(results_path, 'r') as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))

        if not records:
            print(f"\nSkipping {arb_key}: empty results file")
            continue

        df = pd.DataFrame(records)

        # Standardize column names
        if 'final_barrier_code' in df.columns:
            df = df.rename(columns={
                'final_barrier_code': 'arbitrated_barrier',
                'final_feasibility': 'arbitrated_feasibility',
                'adjudication_source': 'arbitration_source'
            })

        arbitrator_data[arb_key] = {
            'df': df,
            'model': model,
            'n_arbitrated': len(df)
        }

        print(f"\nLoaded {arb_key}: {len(df)} arbitration results")
        print(f"  Model: {model}")

    if len(arbitrator_data) < 2:
        print("\nNeed at least 2 arbitrators for comparison.")
        return {'error': 'insufficient_data'}

    results = {
        'arbitrators': list(arbitrator_data.keys()),
        'pairwise_agreement': {},
        'source_preferences': {},
        'barrier_patterns': {},
    }

    # Pairwise agreement between arbitrators
    print("\n" + "-"*50)
    print("PAIRWISE ARBITRATOR AGREEMENT")
    print("-"*50)

    arb_keys = list(arbitrator_data.keys())
    for i, arb1 in enumerate(arb_keys):
        for arb2 in arb_keys[i+1:]:
            df1 = arbitrator_data[arb1]['df']
            df2 = arbitrator_data[arb2]['df']

            # Barrier agreement
            barrier_agree = calculate_agreement(
                df1, df2, 'arbitrated_barrier', 'pair_id'
            )

            # Feasibility agreement
            feas_agree = calculate_agreement(
                df1, df2, 'arbitrated_feasibility', 'pair_id'
            )

            pair_key = f'{arb1}_vs_{arb2}'
            results['pairwise_agreement'][pair_key] = {
                'barrier': barrier_agree,
                'feasibility': feas_agree
            }

            print(f"\n{arb1} vs {arb2}:")
            print(f"  Barrier agreement: {barrier_agree['agreement']*100:.1f}% "
                  f"({barrier_agree['n_agree']}/{barrier_agree['n_common']})")
            print(f"  Feasibility agreement: {feas_agree['agreement']*100:.1f}% "
                  f"({feas_agree['n_agree']}/{feas_agree['n_common']})")

    # Source preference analysis
    print("\n" + "-"*50)
    print("SOURCE PREFERENCES")
    print("-"*50)

    for arb_key, data in arbitrator_data.items():
        prefs = analyze_source_preferences(data['df'], arb_key)
        results['source_preferences'][arb_key] = prefs

        if prefs:
            print(f"\n{arb_key} ({data['model']}):")
            for source, info in prefs.get('source_distribution', {}).items():
                print(f"  {source}: {info['count']} ({info['pct']:.1f}%)")

    # Barrier pattern analysis
    print("\n" + "-"*50)
    print("BARRIER PATTERNS BY ARBITRATOR")
    print("-"*50)

    for arb_key, data in arbitrator_data.items():
        patterns = analyze_barrier_patterns(data['df'], arb_key)
        results['barrier_patterns'][arb_key] = patterns

        if patterns.get('barrier_distribution'):
            print(f"\n{arb_key}:")
            for barrier, count in sorted(patterns['barrier_distribution'].items()):
                print(f"  {barrier}: {count}")

    # Disagreement analysis
    if len(arb_keys) >= 2:
        print("\n" + "-"*50)
        print("SPECIFIC DISAGREEMENTS")
        print("-"*50)

        arb1, arb2 = arb_keys[0], arb_keys[1]
        df1 = arbitrator_data[arb1]['df']
        df2 = arbitrator_data[arb2]['df']

        merged = df1[['pair_id', 'arbitrated_barrier', 'arbitrated_feasibility']].merge(
            df2[['pair_id', 'arbitrated_barrier', 'arbitrated_feasibility']],
            on='pair_id',
            suffixes=(f'_{arb1}', f'_{arb2}')
        )

        if len(merged) > 0:
            # Find barrier disagreements
            barrier_disagree = merged[
                merged[f'arbitrated_barrier_{arb1}'] != merged[f'arbitrated_barrier_{arb2}']
            ]

            print(f"\nBarrier code disagreements: {len(barrier_disagree)}")

            if len(barrier_disagree) > 0:
                # Count disagreement patterns
                patterns = list(zip(
                    barrier_disagree[f'arbitrated_barrier_{arb1}'],
                    barrier_disagree[f'arbitrated_barrier_{arb2}']
                ))
                pattern_counts = Counter(patterns)

                print("\nMost common disagreement patterns:")
                for (b1, b2), count in pattern_counts.most_common(10):
                    print(f"  {arb1}:{b1} vs {arb2}:{b2} = {count}")

                results['disagreement_patterns'] = [
                    {f'{arb1}': b1, f'{arb2}': b2, 'count': count}
                    for (b1, b2), count in pattern_counts.most_common(10)
                ]

            # Feasibility disagreements
            feas_disagree = merged[
                merged[f'arbitrated_feasibility_{arb1}'] != merged[f'arbitrated_feasibility_{arb2}']
            ]

            print(f"\nFeasibility disagreements: {len(feas_disagree)}")

    # Summary statistics
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)

    for arb_key, data in arbitrator_data.items():
        print(f"\n{arb_key}:")
        print(f"  Model: {data['model']}")
        print(f"  Total arbitrated: {data['n_arbitrated']}")

        prefs = results['source_preferences'].get(arb_key, {})
        if prefs.get('source_distribution'):
            synthesis_pct = prefs['source_distribution'].get('synthesis', {}).get('pct', 0)
            print(f"  Synthesis rate: {synthesis_pct:.1f}%")

    # Save results
    comparison_path = analysis_dir / 'arbitrator_comparison.json'
    with open(comparison_path, 'w') as f:
        # Convert DataFrames aren't in results, just dicts
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults saved: {comparison_path}")

    return results


# =============================================================================
# STANDALONE MODE
# =============================================================================

def main():
    """Standalone execution for testing."""
    import yaml

    print("="*60)
    print("ARBITRATOR COMPARISON ANALYSIS v2.0")
    print("="*60)

    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        print(f"ERROR: {config_path} not found")
        return

    with open(config_path) as f:
        config = yaml.safe_load(f)

    results = run_arbitrator_comparison(config)

    print("\n" + "="*60)
    print("COMPARISON COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()
