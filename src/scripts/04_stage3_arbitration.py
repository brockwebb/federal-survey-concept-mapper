#!/usr/bin/env python3
"""
Stage 3 Arbitration Analysis

Computes inter-arbitrator agreement, bias detection, arbitrator-rater concordance,
by-survey barrier breakdowns, and final verdict construction.

Per cc_tasks/CLAUDE_CODE_TASK_stage3_arbitration.md

Input:
  - arbitration_deduped_{openai,anthropic,google}.jsonl
  - barrier_coding_merged_3rater.csv

Output:
  - stage3_arbitration_metrics.json
  - stage3_arbitration_report.md
  - final_verdicts.csv
  - barrier_summary_by_survey.csv
  - confusion_matrices/arbitrator_confusion_*.csv
"""
import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter

# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
from lib.stats import (
    cohens_kappa,
    fleiss_kappa,
    percent_agreement,
    krippendorff_alpha,
    interpret_kappa_mchugh,
)
from lib.taxonomy import extract_l1
from lib.io_utils import ensure_dir

# Scipy for chi-square
from scipy.stats import chisquare

ARBITRATORS = ['openai', 'anthropic', 'google']
ABBREV = {'openai': 'OA', 'anthropic': 'AN', 'google': 'GO'}

# ---------------------------------------------------------------------------
# Step 1: Load and Validate Data
# ---------------------------------------------------------------------------

def load_arbitration_data(base_dir):
    """Load all arbitration JSONL files and rater data."""
    analysis_dir = base_dir / "output" / "report_03" / "analysis"

    arb = {}
    for name in ARBITRATORS:
        path = analysis_dir / f'arbitration_deduped_{name}.jsonl'
        if path.exists():
            df = pd.read_json(path, lines=True)
            df['L1'] = df['final_barrier_code'].apply(extract_l1)
            df['survey'] = df['pair_id'].str.split('_').str[0]
            arb[name] = df
            print(f"  {name}: {len(df)} records")
        else:
            print(f"  {name}: FILE NOT FOUND ({path})")

    # Load rater data
    rater_path = analysis_dir / 'barrier_coding_merged_3rater.csv'
    raters = pd.read_csv(rater_path)
    print(f"  Rater data: {len(raters)} rows")

    return arb, raters


def validate_data(arb, raters):
    """Run validation checks on loaded data."""
    checks = {}

    # Check counts
    checks['openai_count'] = len(arb.get('openai', []))
    checks['anthropic_count'] = len(arb.get('anthropic', []))
    checks['google_count'] = len(arb.get('google', []))
    checks['rater_count'] = len(raters)

    # Check L1 validity
    valid_l1 = {'CC', 'TC', 'RS', 'PC', 'MC', 'PM', 'NHB'}
    for name, df in arb.items():
        null_l1 = df['L1'].isna().sum()
        invalid_l1 = (~df['L1'].isin(valid_l1)).sum() - null_l1
        checks[f'{name}_null_L1'] = int(null_l1)
        checks[f'{name}_invalid_L1'] = int(invalid_l1)

    # Check feasibility values
    valid_feas = {'F1', 'F2', 'F3'}
    for name, df in arb.items():
        invalid_feas = (~df['final_feasibility'].isin(valid_feas)).sum()
        checks[f'{name}_invalid_feasibility'] = int(invalid_feas)

    # Google should be CPS-only
    if 'google' in arb:
        go_surveys = arb['google']['survey'].unique().tolist()
        checks['google_surveys'] = go_surveys
        checks['google_cps_only'] = go_surveys == ['CPS']

    return checks


# ---------------------------------------------------------------------------
# Step 2: Two-Way Inter-Arbitrator Agreement (Full Coverage)
# ---------------------------------------------------------------------------

def compute_two_way_agreement(arb):
    """Compute pairwise agreement between OpenAI and Anthropic arbitrators."""
    if 'openai' not in arb or 'anthropic' not in arb:
        return {"error": "Missing OpenAI or Anthropic arbitration data"}

    oa = arb['openai'][['pair_id', 'final_barrier_code', 'final_feasibility', 'L1']].copy()
    an = arb['anthropic'][['pair_id', 'final_barrier_code', 'final_feasibility', 'L1']].copy()

    merged = oa.merge(an, on='pair_id', suffixes=('_oa', '_an'))
    n = len(merged)

    results = {
        "n_pairs": n,
        "coverage": "full (all 1,598 pairs)"
    }

    # L1 agreement
    l1_pct = percent_agreement(merged['L1_oa'].values, merged['L1_an'].values)
    l1_kappa = cohens_kappa(merged['L1_oa'].values, merged['L1_an'].values)
    l1_interp, l1_passed = interpret_kappa_mchugh(l1_kappa)
    results['L1'] = {
        "percent_agreement": round(float(l1_pct * 100), 1),
        "cohens_kappa": round(float(l1_kappa), 3),
        "interpretation": l1_interp,
        "quality_gate_passed": l1_passed
    }

    # Full barrier code agreement
    bc_pct = percent_agreement(
        merged['final_barrier_code_oa'].values,
        merged['final_barrier_code_an'].values
    )
    bc_kappa = cohens_kappa(
        merged['final_barrier_code_oa'].values,
        merged['final_barrier_code_an'].values
    )
    bc_interp, bc_passed = interpret_kappa_mchugh(bc_kappa)
    results['full_barrier_code'] = {
        "percent_agreement": round(float(bc_pct * 100), 1),
        "cohens_kappa": round(float(bc_kappa), 3),
        "interpretation": bc_interp,
        "quality_gate_passed": bc_passed
    }

    # Feasibility agreement
    f_pct = percent_agreement(
        merged['final_feasibility_oa'].values,
        merged['final_feasibility_an'].values
    )
    f_kappa = cohens_kappa(
        merged['final_feasibility_oa'].values,
        merged['final_feasibility_an'].values
    )
    f_interp, f_passed = interpret_kappa_mchugh(f_kappa)
    results['feasibility'] = {
        "percent_agreement": round(float(f_pct * 100), 1),
        "cohens_kappa": round(float(f_kappa), 3),
        "interpretation": f_interp,
        "quality_gate_passed": f_passed
    }

    # Binary consolidability
    merged['consol_oa'] = merged['final_feasibility_oa'].apply(
        lambda x: 'Consolidable' if x in ('F1', 'F2') else 'Not_Consolidable'
    )
    merged['consol_an'] = merged['final_feasibility_an'].apply(
        lambda x: 'Consolidable' if x in ('F1', 'F2') else 'Not_Consolidable'
    )
    bc_pct = percent_agreement(merged['consol_oa'].values, merged['consol_an'].values)
    bc_kappa = cohens_kappa(merged['consol_oa'].values, merged['consol_an'].values)
    bc_interp, bc_passed = interpret_kappa_mchugh(bc_kappa)
    results['binary_consolidability'] = {
        "percent_agreement": round(float(bc_pct * 100), 1),
        "cohens_kappa": round(float(bc_kappa), 3),
        "interpretation": bc_interp,
        "quality_gate_passed": bc_passed
    }

    return results


# ---------------------------------------------------------------------------
# Step 3: Three-Way Inter-Arbitrator Agreement (CPS Subset)
# ---------------------------------------------------------------------------

def compute_three_way_agreement(arb):
    """Compute three-way agreement on subset with all arbitrators."""
    if not all(k in arb for k in ARBITRATORS):
        return {"error": "Missing one or more arbitrator datasets"}

    # Find common pairs
    common_pairs = (
        set(arb['openai']['pair_id']) &
        set(arb['anthropic']['pair_id']) &
        set(arb['google']['pair_id'])
    )

    results = {
        "n_pairs": len(common_pairs),
        "coverage": "CPS subset only (Google limited)"
    }

    # Filter each
    filtered = {}
    for name in ARBITRATORS:
        df = arb[name][arb[name]['pair_id'].isin(common_pairs)].copy()
        df = df.sort_values('pair_id').reset_index(drop=True)
        filtered[name] = df

    # Verify alignment
    assert list(filtered['openai']['pair_id']) == list(filtered['anthropic']['pair_id'])
    assert list(filtered['openai']['pair_id']) == list(filtered['google']['pair_id'])

    # L1 three-way
    l1_matrix = np.column_stack([
        filtered[name]['L1'].astype(str).values for name in ARBITRATORS
    ])
    l1_fleiss = fleiss_kappa(l1_matrix)
    l1_alpha = krippendorff_alpha(l1_matrix)
    l1_interp, l1_passed = interpret_kappa_mchugh(l1_fleiss)

    results['L1'] = {
        "fleiss_kappa": round(float(l1_fleiss), 3),
        "krippendorff_alpha": round(float(l1_alpha), 3),
        "interpretation": l1_interp,
        "quality_gate_passed": l1_passed
    }

    # L1 pairwise within three-way subset
    l1_pairwise = {}
    pairs = [('openai', 'anthropic'), ('openai', 'google'), ('anthropic', 'google')]
    for r1, r2 in pairs:
        pair_key = f"{ABBREV[r1]}_vs_{ABBREV[r2]}"
        pct = percent_agreement(
            filtered[r1]['L1'].values,
            filtered[r2]['L1'].values
        )
        kappa = cohens_kappa(
            filtered[r1]['L1'].values,
            filtered[r2]['L1'].values
        )
        interp, passed = interpret_kappa_mchugh(kappa)
        l1_pairwise[pair_key] = {
            "percent_agreement": round(float(pct * 100), 1),
            "cohens_kappa": round(float(kappa), 3),
            "interpretation": interp
        }
    results['L1_pairwise'] = l1_pairwise

    # Full barrier code (L2) three-way
    bc_matrix = np.column_stack([
        filtered[name]['final_barrier_code'].astype(str).values for name in ARBITRATORS
    ])
    bc_fleiss = fleiss_kappa(bc_matrix)
    bc_alpha = krippendorff_alpha(bc_matrix)
    bc_interp, bc_passed = interpret_kappa_mchugh(bc_fleiss)

    results['full_barrier_code'] = {
        "fleiss_kappa": round(float(bc_fleiss), 3),
        "krippendorff_alpha": round(float(bc_alpha), 3),
        "interpretation": bc_interp,
        "quality_gate_passed": bc_passed
    }

    # Full barrier code pairwise within three-way subset
    bc_pairwise = {}
    for r1, r2 in pairs:
        pair_key = f"{ABBREV[r1]}_vs_{ABBREV[r2]}"
        pct = percent_agreement(
            filtered[r1]['final_barrier_code'].values,
            filtered[r2]['final_barrier_code'].values
        )
        kappa = cohens_kappa(
            filtered[r1]['final_barrier_code'].values,
            filtered[r2]['final_barrier_code'].values
        )
        interp, passed = interpret_kappa_mchugh(kappa)
        bc_pairwise[pair_key] = {
            "percent_agreement": round(float(pct * 100), 1),
            "cohens_kappa": round(float(kappa), 3),
            "interpretation": interp
        }
    results['full_barrier_code_pairwise'] = bc_pairwise

    # Feasibility three-way
    feas_matrix = np.column_stack([
        filtered[name]['final_feasibility'].astype(str).values for name in ARBITRATORS
    ])
    feas_fleiss = fleiss_kappa(feas_matrix)
    feas_alpha = krippendorff_alpha(feas_matrix)
    feas_interp, feas_passed = interpret_kappa_mchugh(feas_fleiss)

    results['feasibility'] = {
        "fleiss_kappa": round(float(feas_fleiss), 3),
        "krippendorff_alpha": round(float(feas_alpha), 3),
        "interpretation": feas_interp,
        "quality_gate_passed": feas_passed
    }

    # Binary consolidability three-way
    consol_matrix = np.column_stack([
        filtered[name]['final_feasibility'].apply(
            lambda x: 'Consolidable' if x in ('F1', 'F2') else 'Not_Consolidable'
        ).values for name in ARBITRATORS
    ])
    consol_fleiss = fleiss_kappa(consol_matrix)
    consol_alpha = krippendorff_alpha(consol_matrix)
    consol_interp, consol_passed = interpret_kappa_mchugh(consol_fleiss)

    results['binary_consolidability'] = {
        "fleiss_kappa": round(float(consol_fleiss), 3),
        "krippendorff_alpha": round(float(consol_alpha), 3),
        "interpretation": consol_interp,
        "quality_gate_passed": consol_passed
    }

    return results


# ---------------------------------------------------------------------------
# Step 4: Arbitrator-Rater Concordance
# ---------------------------------------------------------------------------

def compute_arbitrator_rater_concordance(arb, raters):
    """How often does arbitrator verdict match rater majority vote?"""
    # Prepare rater data with L1
    raters = raters.copy()
    for r in ['openai', 'anthropic', 'google']:
        raters[f'L1_{r}'] = raters[f'primary_barrier_{r}'].apply(extract_l1)

    results = {}

    for arb_name, arb_df in arb.items():
        arb_merged = arb_df[['pair_id', 'final_barrier_code', 'final_feasibility', 'L1']].merge(
            raters[['pair_id',
                     'L1_openai', 'L1_anthropic', 'L1_google',
                     'primary_barrier_openai', 'primary_barrier_anthropic', 'primary_barrier_google',
                     'feasibility_openai', 'feasibility_anthropic', 'feasibility_google']],
            on='pair_id',
            how='inner'
        )

        n = len(arb_merged)

        # Majority vote functions
        def majority(row, cols):
            votes = [row[c] for c in cols]
            counts = Counter(votes)
            most_common = counts.most_common(1)[0]
            return most_common[0] if most_common[1] >= 2 else None

        def is_unanimous(row, cols):
            votes = [row[c] for c in cols]
            return len(set(votes)) == 1

        l1_cols = ['L1_openai', 'L1_anthropic', 'L1_google']
        l2_cols = ['primary_barrier_openai', 'primary_barrier_anthropic', 'primary_barrier_google']
        feas_cols = ['feasibility_openai', 'feasibility_anthropic', 'feasibility_google']

        arb_merged['rater_L1_majority'] = arb_merged.apply(
            lambda r: majority(r, l1_cols), axis=1
        )
        arb_merged['rater_L2_majority'] = arb_merged.apply(
            lambda r: majority(r, l2_cols), axis=1
        )
        arb_merged['rater_feas_majority'] = arb_merged.apply(
            lambda r: majority(r, feas_cols), axis=1
        )
        arb_merged['rater_L1_unanimous'] = arb_merged.apply(
            lambda r: is_unanimous(r, l1_cols), axis=1
        )
        arb_merged['rater_L2_unanimous'] = arb_merged.apply(
            lambda r: is_unanimous(r, l2_cols), axis=1
        )
        arb_merged['rater_feas_unanimous'] = arb_merged.apply(
            lambda r: is_unanimous(r, feas_cols), axis=1
        )

        # Concordance with majority
        has_l1_majority = arb_merged['rater_L1_majority'].notna()
        l1_match_majority = (
            arb_merged.loc[has_l1_majority, 'L1'] ==
            arb_merged.loc[has_l1_majority, 'rater_L1_majority']
        ).mean()

        has_l2_majority = arb_merged['rater_L2_majority'].notna()
        l2_match_majority = (
            arb_merged.loc[has_l2_majority, 'final_barrier_code'] ==
            arb_merged.loc[has_l2_majority, 'rater_L2_majority']
        ).mean()

        has_feas_majority = arb_merged['rater_feas_majority'].notna()
        feas_match_majority = (
            arb_merged.loc[has_feas_majority, 'final_feasibility'] ==
            arb_merged.loc[has_feas_majority, 'rater_feas_majority']
        ).mean()

        # Concordance with unanimous
        unanimous_l1 = arb_merged[arb_merged['rater_L1_unanimous']]
        l1_match_unanimous = (
            unanimous_l1['L1'] == unanimous_l1['rater_L1_majority']
        ).mean() if len(unanimous_l1) > 0 else np.nan

        unanimous_l2 = arb_merged[arb_merged['rater_L2_unanimous']]
        l2_match_unanimous = (
            unanimous_l2['final_barrier_code'] == unanimous_l2['rater_L2_majority']
        ).mean() if len(unanimous_l2) > 0 else np.nan

        unanimous_feas = arb_merged[arb_merged['rater_feas_unanimous']]
        feas_match_unanimous = (
            unanimous_feas['final_feasibility'] == unanimous_feas['rater_feas_majority']
        ).mean() if len(unanimous_feas) > 0 else np.nan

        # Override rate: how often does arbitrator disagree with unanimous raters?
        l1_override_count = int(
            (unanimous_l1['L1'] != unanimous_l1['rater_L1_majority']).sum()
        ) if len(unanimous_l1) > 0 else 0

        l2_override_count = int(
            (unanimous_l2['final_barrier_code'] != unanimous_l2['rater_L2_majority']).sum()
        ) if len(unanimous_l2) > 0 else 0

        feas_override_count = int(
            (unanimous_feas['final_feasibility'] != unanimous_feas['rater_feas_majority']).sum()
        ) if len(unanimous_feas) > 0 else 0

        results[arb_name] = {
            "n_pairs": n,
            "L1_concordance_with_majority_pct": round(float(l1_match_majority * 100), 1),
            "L2_concordance_with_majority_pct": round(float(l2_match_majority * 100), 1),
            "feasibility_concordance_with_majority_pct": round(float(feas_match_majority * 100), 1),
            "L1_concordance_with_unanimous_pct": round(float(l1_match_unanimous * 100), 1)
                if not np.isnan(l1_match_unanimous) else None,
            "L2_concordance_with_unanimous_pct": round(float(l2_match_unanimous * 100), 1)
                if not np.isnan(l2_match_unanimous) else None,
            "feasibility_concordance_with_unanimous_pct": round(float(feas_match_unanimous * 100), 1)
                if not np.isnan(feas_match_unanimous) else None,
            "n_unanimous_L1_cases": len(unanimous_l1),
            "L1_overrides_of_unanimous": l1_override_count,
            "n_unanimous_L2_cases": len(unanimous_l2),
            "L2_overrides_of_unanimous": l2_override_count,
            "n_unanimous_feas_cases": len(unanimous_feas),
            "feas_overrides_of_unanimous": feas_override_count
        }

    return results


# ---------------------------------------------------------------------------
# Step 4b: Synthesis Detection
# ---------------------------------------------------------------------------

def compute_synthesis_detection(arb, raters):
    """Compute synthesis behavior stratified by rater agreement, per arbitrator.

    Per SPEC_R03_S3_001_AMENDMENT_A:
    - Synthesis = selected_rater_key == "synthesis" (LITERAL, not outcome-based)
    - Stratify by whether raters were unanimous or split

    Confusion matrix:
    - TP: Raters unanimous AND arbitrator synthesized
    - FN: Raters unanimous AND arbitrator did NOT synthesize
    - FP: Raters NOT unanimous AND arbitrator synthesized
    - TN: Raters NOT unanimous AND arbitrator did NOT synthesize
    """
    # Prep rater data - check unanimity on L1
    rater_df = raters.copy()
    for r in ['openai', 'anthropic', 'google']:
        rater_df[f'L1_{r}'] = rater_df[f'primary_barrier_{r}'].apply(extract_l1)

    def is_unanimous(row):
        votes = [row['L1_openai'], row['L1_anthropic'], row['L1_google']]
        valid = [v for v in votes if pd.notna(v)]
        if len(valid) < 2:
            return None
        return len(set(valid)) == 1

    rater_df['raters_unanimous'] = rater_df.apply(is_unanimous, axis=1)

    results = {}

    for arb_name, arb_df in arb.items():
        merged = arb_df[['pair_id', 'selected_rater', 'selected_rater_key']].merge(
            rater_df[['pair_id', 'raters_unanimous']],
            on='pair_id',
            how='inner'
        )

        # Use selected_rater (raw field) to determine synthesis.
        # selected_rater_key has a known upstream bug where Google's "Rater A/B/C"
        # values are mapped to "synthesis" instead of the vendor name.
        merged['arb_synthesized'] = merged['selected_rater'].apply(
            lambda v: str(v).strip().lower() in ('synthesis', 'syn') if pd.notna(v) else False
        )

        # Filter to rows with valid unanimity determination
        valid = merged[merged['raters_unanimous'].notna()].copy()

        unanimous = valid[valid['raters_unanimous'] == True]
        split = valid[valid['raters_unanimous'] == False]

        n_unanimous = len(unanimous)
        n_split = len(split)

        synth_when_unanimous = int(unanimous['arb_synthesized'].sum()) if n_unanimous > 0 else 0
        synth_when_split = int(split['arb_synthesized'].sum()) if n_split > 0 else 0

        rate_unanimous = round(synth_when_unanimous / n_unanimous * 100, 1) if n_unanimous > 0 else None
        rate_split = round(synth_when_split / n_split * 100, 1) if n_split > 0 else None

        # Confusion matrix
        TP = synth_when_unanimous
        FN = n_unanimous - synth_when_unanimous
        FP = synth_when_split
        TN = n_split - synth_when_split

        precision = TP / (TP + FP) if (TP + FP) > 0 else 0.0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        total_synth = TP + FP
        total_n = len(valid)
        synthesis_rate_overall = round(total_synth / total_n * 100, 1) if total_n > 0 else 0

        pattern = classify_synthesis_pattern(rate_unanimous, rate_split)

        results[arb_name] = {
            'n_pairs': total_n,
            'n_raters_unanimous': n_unanimous,
            'n_raters_split': n_split,
            'synthesis_when_unanimous': {
                'n': n_unanimous,
                'synthesis_count': TP,
                'rate_pct': rate_unanimous
            },
            'synthesis_when_split': {
                'n': n_split,
                'synthesis_count': FP,
                'rate_pct': rate_split
            },
            'confusion_matrix': {
                'TP': TP,
                'FN': FN,
                'FP': FP,
                'TN': TN
            },
            'precision': round(float(precision), 3),
            'recall': round(float(recall), 3),
            'f1': round(float(f1), 3),
            'synthesis_rate_overall': synthesis_rate_overall,
            'interpretation': pattern
        }

    return results


def classify_synthesis_pattern(unanimous_rate, split_rate):
    """Classify synthesis behavior pattern per Amendment A.

    Patterns:
    - efficient: Low unanimous (<30%), high split (>50%)
    - always_synthesizes: High unanimous (>70%), high split (>70%)
    - deferential: Low unanimous (<30%), low split (<30%)
    - backwards: Unanimous rate > split rate by >20pp
    - moderate: Everything else
    """
    if unanimous_rate is None or split_rate is None:
        return "insufficient_data"

    u = unanimous_rate / 100
    s = split_rate / 100

    if u < 0.30 and s > 0.50:
        return "efficient"
    elif u > 0.70 and s > 0.70:
        return "always_synthesizes"
    elif u < 0.30 and s < 0.30:
        return "deferential"
    elif u > s + 0.20:
        return "backwards"
    else:
        return "moderate"


def validate_synthesis_consistency(synthesis_metrics, position_bias_metrics):
    """Ensure synthesis rates match between sections (per Amendment A Section 6.3)."""
    errors = []
    for arb_name in ['openai', 'anthropic', 'google']:
        if arb_name not in synthesis_metrics or arb_name not in position_bias_metrics:
            continue
        synth_rate_detection = synthesis_metrics[arb_name]['synthesis_rate_overall']
        synth_rate_position = position_bias_metrics[arb_name]['synthesis_rate']

        if abs(synth_rate_detection - synth_rate_position) > 0.5:
            errors.append(
                f"{arb_name}: synthesis_detection says {synth_rate_detection}%, "
                f"position_bias says {synth_rate_position}%"
            )

    if errors:
        raise ValueError("Synthesis rate mismatch!\n" + "\n".join(errors))

    print("  Synthesis rate consistency validated")


# ---------------------------------------------------------------------------
# Step 5: Bias Detection
# ---------------------------------------------------------------------------

def normalize_position(val):
    """Normalize selected_rater to A/B/C/synthesis."""
    if pd.isna(val):
        return None
    val = str(val).strip()
    val_lower = val.lower()
    if val_lower in ('synthesis', 'syn'):
        return 'synthesis'
    # Match exact single letters or "Rater X" format
    if val in ('A', 'B', 'C'):
        return val
    if val_lower.startswith('rater ') and len(val_lower) == 8:
        return val_lower[-1].upper()
    # Fallback: check last character
    if val_lower.endswith((' a', ' b', ' c')):
        return val_lower[-1].upper()
    return val


def analyze_position_bias(arb):
    """Analyze position selection patterns per arbitrator."""
    results = {}

    for name, df in arb.items():
        df = df.copy()
        df['position'] = df['selected_rater'].apply(normalize_position)

        position_counts = df['position'].value_counts().to_dict()

        # Only test A/B/C uniformity (exclude synthesis)
        abc_counts = [position_counts.get(p, 0) for p in ['A', 'B', 'C']]
        n_non_synth = sum(abc_counts)

        chi2_result = None
        if n_non_synth >= 10 and all(c > 0 for c in abc_counts):
            expected = [n_non_synth / 3] * 3
            chi2, p = chisquare(abc_counts, expected)
            chi2_result = {
                "chi_square": round(float(chi2), 3),
                "p_value": round(float(p), 4),
                "significant_at_05": bool(p < 0.05),
                "observed": dict(zip(['A', 'B', 'C'], [int(c) for c in abc_counts])),
                "expected_each": round(n_non_synth / 3, 1)
            }

        synthesis_rate = position_counts.get('synthesis', 0) / len(df)

        results[name] = {
            "n_total": len(df),
            "position_counts": {k: int(v) for k, v in position_counts.items()},
            "synthesis_rate": round(float(synthesis_rate * 100), 1),
            "n_non_synthesis": n_non_synth,
            "chi_square_test": chi2_result
        }

    return results


def analyze_family_bias(arb):
    """Check if arbitrator favors same-vendor rater."""
    results = {}

    for name, df in arb.items():
        df = df.copy()

        # Use selected_rater_key which already maps to vendor names
        # Exclude synthesis cases
        non_synth = df[df['selected_rater_key'] != 'synthesis'].copy()
        n = len(non_synth)

        if n == 0:
            results[name] = {"n_non_synthesis": 0, "note": "All synthesis"}
            continue

        same_family = (non_synth['selected_rater_key'] == name).sum()
        same_family_rate = same_family / n

        # Chi-square: observed same-family vs expected 33.3%
        expected_same = n / 3
        expected_other = n * 2 / 3
        observed = [int(same_family), int(n - same_family)]
        expected = [expected_same, expected_other]

        chi2, p = chisquare(observed, expected)

        results[name] = {
            "n_non_synthesis": n,
            "same_family_selected": int(same_family),
            "same_family_rate_pct": round(float(same_family_rate * 100), 1),
            "expected_rate_pct": 33.3,
            "chi_square": round(float(chi2), 3),
            "p_value": round(float(p), 4),
            "significant_at_05": bool(p < 0.05),
            "rater_selection_breakdown": {
                k: int(v) for k, v in
                non_synth['selected_rater_key'].value_counts().items()
            }
        }

    return results


# ---------------------------------------------------------------------------
# Step 6: By-Survey Barrier Breakdown
# ---------------------------------------------------------------------------

def barrier_summary_by_survey(verdicts_df):
    """Generate barrier distribution by survey."""
    results = {}

    for survey in sorted(verdicts_df['survey'].unique()):
        subset = verdicts_df[verdicts_df['survey'] == survey]

        l1_counts = subset['final_L1'].value_counts()
        l1_pcts = (subset['final_L1'].value_counts(normalize=True) * 100).round(1)

        feas_counts = subset['final_feasibility'].value_counts()
        feas_pcts = (subset['final_feasibility'].value_counts(normalize=True) * 100).round(1)

        # Binary consolidability
        consol = subset['final_feasibility'].apply(
            lambda x: 'Consolidable' if x in ('F1', 'F2') else 'Not_Consolidable'
        )
        consol_counts = consol.value_counts()

        # Top L2 barriers
        top_l2 = subset['final_barrier_code'].value_counts().head(5)

        results[survey] = {
            "n_pairs": len(subset),
            "L1_distribution": {k: int(v) for k, v in l1_counts.items()},
            "L1_percentages": {k: float(v) for k, v in l1_pcts.items()},
            "feasibility_distribution": {k: int(v) for k, v in feas_counts.items()},
            "feasibility_percentages": {k: float(v) for k, v in feas_pcts.items()},
            "binary_consolidability": {k: int(v) for k, v in consol_counts.items()},
            "top_L2_barriers": {k: int(v) for k, v in top_l2.items()}
        }

    return results


# ---------------------------------------------------------------------------
# Step 7: Final Verdict Construction
# ---------------------------------------------------------------------------

def construct_final_verdicts(arb):
    """Build final verdicts with confidence levels.

    Strategy:
    - Two-way (OA+AN): covers all 1,598 pairs
    - Three-way pairs get additional confidence from Google
    - OpenAI as tiebreaker for two-way disagreements (documented choice)
    """
    oa = arb['openai'][['pair_id', 'final_barrier_code', 'final_feasibility',
                         'L1', 'survey', 'reasoning']].copy()
    an = arb['anthropic'][['pair_id', 'final_barrier_code', 'final_feasibility',
                            'L1', 'reasoning']].copy()

    merged = oa.merge(an, on='pair_id', suffixes=('_oa', '_an'))

    # Agreement checks
    merged['L1_agree_oa_an'] = merged['L1_oa'] == merged['L1_an']
    merged['feas_agree_oa_an'] = (
        merged['final_feasibility_oa'] == merged['final_feasibility_an']
    )

    # Add Google where available
    has_google = 'google' in arb and len(arb['google']) > 0
    if has_google:
        go = arb['google'][['pair_id', 'final_barrier_code', 'final_feasibility',
                             'L1']].copy()
        merged = merged.merge(
            go, on='pair_id', suffixes=('', '_go'), how='left'
        )
        # Rename google columns
        merged.rename(columns={
            'final_barrier_code': 'final_barrier_code_go',
            'final_feasibility': 'final_feasibility_go',
            'L1': 'L1_go'
        }, inplace=True)
        merged['has_google'] = merged['L1_go'].notna()
    else:
        merged['has_google'] = False

    # Determine final verdict
    def resolve_verdict(row):
        """Resolve final L1 and feasibility."""
        # L1
        if row['L1_agree_oa_an']:
            final_l1 = row['L1_oa']
        elif row['has_google'] and pd.notna(row.get('L1_go')):
            # Three-way majority
            votes = [row['L1_oa'], row['L1_an'], row['L1_go']]
            counts = Counter(votes)
            most_common = counts.most_common(1)[0]
            if most_common[1] >= 2:
                final_l1 = most_common[0]
            else:
                final_l1 = row['L1_oa']  # OA tiebreak
        else:
            final_l1 = row['L1_oa']  # OA tiebreak

        # Feasibility
        if row['feas_agree_oa_an']:
            final_feas = row['final_feasibility_oa']
        elif row['has_google'] and pd.notna(row.get('final_feasibility_go')):
            votes = [
                row['final_feasibility_oa'],
                row['final_feasibility_an'],
                row['final_feasibility_go']
            ]
            counts = Counter(votes)
            most_common = counts.most_common(1)[0]
            if most_common[1] >= 2:
                final_feas = most_common[0]
            else:
                final_feas = row['final_feasibility_oa']  # OA tiebreak
        else:
            final_feas = row['final_feasibility_oa']  # OA tiebreak

        # Barrier code: use the one matching final L1
        if row['L1_oa'] == final_l1:
            final_code = row['final_barrier_code_oa']
        elif row['L1_an'] == final_l1:
            final_code = row['final_barrier_code_an']
        elif row['has_google'] and pd.notna(row.get('L1_go')) and row['L1_go'] == final_l1:
            final_code = row['final_barrier_code_go']
        else:
            final_code = row['final_barrier_code_oa']  # fallback

        return pd.Series({
            'final_L1': final_l1,
            'final_feasibility': final_feas,
            'final_barrier_code': final_code
        })

    verdicts = merged.apply(resolve_verdict, axis=1)
    merged = pd.concat([merged, verdicts], axis=1)

    # Confidence levels
    def get_confidence(row):
        oa_an_agree = row['L1_agree_oa_an'] and row['feas_agree_oa_an']

        if oa_an_agree and row['has_google']:
            # Check if Google also agrees
            go_l1_agree = row.get('L1_go') == row['final_L1']
            go_feas_agree = row.get('final_feasibility_go') == row['final_feasibility']
            if go_l1_agree and go_feas_agree:
                return 'HIGH'  # All three agree
            else:
                return 'HIGH'  # Two-way agreement still sufficient
        elif oa_an_agree:
            return 'HIGH'
        elif row['L1_agree_oa_an'] or row['feas_agree_oa_an']:
            return 'MODERATE'
        else:
            return 'LOW'

    merged['confidence'] = merged.apply(get_confidence, axis=1)

    return merged


# ---------------------------------------------------------------------------
# Confusion Matrices
# ---------------------------------------------------------------------------

def compute_confusion_matrices(arb, output_dir):
    """Generate arbitrator confusion matrices for L1 and feasibility."""
    ensure_dir(output_dir)
    pairs = [('openai', 'anthropic')]

    # Add Google pairs if available
    if 'google' in arb:
        pairs.extend([('openai', 'google'), ('anthropic', 'google')])

    saved = []
    for r1, r2 in pairs:
        common = set(arb[r1]['pair_id']) & set(arb[r2]['pair_id'])
        df1 = arb[r1][arb[r1]['pair_id'].isin(common)].sort_values('pair_id')
        df2 = arb[r2][arb[r2]['pair_id'].isin(common)].sort_values('pair_id')

        # L1 confusion
        l1_cats = sorted(set(df1['L1'].dropna()) | set(df2['L1'].dropna()))
        cm = pd.crosstab(
            df1['L1'].values,
            df2['L1'].values,
            rownames=[f'{ABBREV[r1]}'],
            colnames=[f'{ABBREV[r2]}']
        )
        fname = f"arbitrator_confusion_L1_{ABBREV[r1]}_{ABBREV[r2]}.csv"
        cm.to_csv(output_dir / fname)
        saved.append(fname)

        # Feasibility confusion
        cm_feas = pd.crosstab(
            df1['final_feasibility'].values,
            df2['final_feasibility'].values,
            rownames=[f'{ABBREV[r1]}'],
            colnames=[f'{ABBREV[r2]}']
        )
        fname = f"arbitrator_confusion_feas_{ABBREV[r1]}_{ABBREV[r2]}.csv"
        cm_feas.to_csv(output_dir / fname)
        saved.append(fname)

        # Full barrier code (L2) confusion
        cm_bc = pd.crosstab(
            df1['final_barrier_code'].values,
            df2['final_barrier_code'].values,
            rownames=[f'{ABBREV[r1]}'],
            colnames=[f'{ABBREV[r2]}']
        )
        fname = f"arbitrator_confusion_L2_{ABBREV[r1]}_{ABBREV[r2]}.csv"
        cm_bc.to_csv(output_dir / fname)
        saved.append(fname)

    return saved


# ---------------------------------------------------------------------------
# Step 8: Report Generation
# ---------------------------------------------------------------------------

def generate_report(metrics, output_path):
    """Generate human-readable markdown report."""
    lines = []
    meta = metrics.get('metadata', {})

    lines.append("# Stage 3 Arbitration Analysis Report")
    lines.append("")
    lines.append(f"**Generated:** {meta.get('generated_at', 'N/A')}")
    lines.append(f"**OpenAI pairs:** {meta.get('openai_count', '?'):,}")
    lines.append(f"**Anthropic pairs:** {meta.get('anthropic_count', '?'):,}")
    lines.append(f"**Google pairs:** {meta.get('google_count', '?'):,}")
    lines.append("")

    # --- Executive Summary ---
    lines.append("## 1. Executive Summary")
    lines.append("")
    tw = metrics.get('two_way_agreement', {})
    thw = metrics.get('three_way_agreement', {})
    lines.append(f"- **Two-way (OA vs AN) L1 agreement:** "
                 f"{tw.get('L1', {}).get('percent_agreement', '?')}% "
                 f"(κ={tw.get('L1', {}).get('cohens_kappa', '?')})")
    lines.append(f"- **Two-way feasibility agreement:** "
                 f"{tw.get('feasibility', {}).get('percent_agreement', '?')}% "
                 f"(κ={tw.get('feasibility', {}).get('cohens_kappa', '?')})")
    lines.append(f"- **Two-way binary consolidability:** "
                 f"{tw.get('binary_consolidability', {}).get('percent_agreement', '?')}% "
                 f"(κ={tw.get('binary_consolidability', {}).get('cohens_kappa', '?')})")
    if 'L1' in thw:
        lines.append(f"- **Three-way (CPS subset) L1 Fleiss' κ:** "
                     f"{thw['L1'].get('fleiss_kappa', '?')}")
    fvs = metrics.get('final_verdict_summary', {})
    conf = fvs.get('confidence_distribution', {})
    if conf:
        lines.append(f"- **Final verdicts:** {conf.get('HIGH', 0):,} HIGH, "
                     f"{conf.get('MODERATE', 0):,} MODERATE, {conf.get('LOW', 0):,} LOW")
    sd = metrics.get('synthesis_detection', {})
    if sd:
        f1_scores = [(name, d.get('f1', 0)) for name, d in sd.items()]
        min_f1 = min(f1_scores, key=lambda x: x[1])
        max_f1 = max(f1_scores, key=lambda x: x[1])
        lines.append(f"- **Synthesis detection F1:** {min_f1[0]}={min_f1[1]}, {max_f1[0]}={max_f1[1]}")
        for arb_name in ARBITRATORS:
            if arb_name in sd:
                m = sd[arb_name]
                lines.append(
                    f"- **{arb_name.capitalize()} synthesis pattern:** {m['interpretation']} "
                    f"(unanimous: {m['synthesis_when_unanimous']['rate_pct']}%, "
                    f"split: {m['synthesis_when_split']['rate_pct']}%)")
    lines.append("")

    # --- Two-Way Agreement ---
    lines.append("## 2. Inter-Arbitrator Agreement (Two-Way)")
    lines.append("")
    lines.append(f"**Coverage:** {tw.get('n_pairs', '?'):,} pairs (OpenAI + Anthropic)")
    lines.append("")
    lines.append("| Metric | % Agreement | Cohen's κ | Interpretation | Quality Gate |")
    lines.append("|--------|-------------|-----------|----------------|--------------|")
    for metric in ['L1', 'full_barrier_code', 'feasibility', 'binary_consolidability']:
        d = tw.get(metric, {})
        gate = "PASSED" if d.get('quality_gate_passed') else "NOT PASSED"
        lines.append(f"| {metric} | {d.get('percent_agreement', '?')}% | "
                     f"{d.get('cohens_kappa', '?')} | {d.get('interpretation', '?')} | {gate} |")
    lines.append("")

    # --- Three-Way Agreement ---
    lines.append("## 3. Inter-Arbitrator Agreement (Three-Way)")
    lines.append("")
    lines.append(f"**Coverage:** {thw.get('n_pairs', '?'):,} pairs (CPS only — Google limited)")
    lines.append("")
    if 'L1' in thw:
        lines.append("### Three-Way Metrics")
        lines.append("")
        lines.append("| Metric | Fleiss' κ | Krippendorff's α | Interpretation |")
        lines.append("|--------|-----------|------------------|----------------|")
        for metric in ['L1', 'full_barrier_code', 'feasibility', 'binary_consolidability']:
            d = thw.get(metric, {})
            lines.append(f"| {metric} | {d.get('fleiss_kappa', '?')} | "
                         f"{d.get('krippendorff_alpha', '?')} | {d.get('interpretation', '?')} |")
        lines.append("")

        pw = thw.get('L1_pairwise', {})
        if pw:
            lines.append("### Pairwise L1 (Three-Way Subset)")
            lines.append("")
            lines.append("| Comparison | % Agreement | Cohen's κ | Interpretation |")
            lines.append("|------------|-------------|-----------|----------------|")
            for pair, d in pw.items():
                lines.append(f"| {pair.replace('_', ' ')} | "
                             f"{d.get('percent_agreement', '?')}% | "
                             f"{d.get('cohens_kappa', '?')} | {d.get('interpretation', '?')} |")
            lines.append("")

        # L2 pairwise (if exists)
        pw_bc = thw.get('full_barrier_code_pairwise', {})
        if pw_bc:
            lines.append("### Pairwise L2/Full Barrier Code (Three-Way Subset)")
            lines.append("")
            lines.append("| Comparison | % Agreement | Cohen's κ | Interpretation |")
            lines.append("|------------|-------------|-----------|----------------|")
            for pair, d in pw_bc.items():
                lines.append(f"| {pair.replace('_', ' ')} | "
                             f"{d.get('percent_agreement', '?')}% | "
                             f"{d.get('cohens_kappa', '?')} | {d.get('interpretation', '?')} |")
            lines.append("")

    # --- Concordance ---
    lines.append("## 4. Arbitrator-Rater Concordance")
    lines.append("")
    conc = metrics.get('arbitrator_rater_concordance', {})
    lines.append("| Arbitrator | n | L1 vs Maj | L2 vs Maj | Feas vs Maj | L1 vs Unan | L2 vs Unan | Feas vs Unan | L1 Overrides | L2 Overrides |")
    lines.append("|------------|---|-----------|-----------|-------------|------------|------------|--------------|--------------|--------------|")
    for arb_name in ARBITRATORS:
        d = conc.get(arb_name, {})
        if not d:
            continue
        lines.append(
            f"| {arb_name} | {d.get('n_pairs', '?'):,} | "
            f"{d.get('L1_concordance_with_majority_pct', '?')}% | "
            f"{d.get('L2_concordance_with_majority_pct', '?')}% | "
            f"{d.get('feasibility_concordance_with_majority_pct', '?')}% | "
            f"{d.get('L1_concordance_with_unanimous_pct', 'N/A')}% | "
            f"{d.get('L2_concordance_with_unanimous_pct', 'N/A')}% | "
            f"{d.get('feasibility_concordance_with_unanimous_pct', 'N/A')}% | "
            f"{d.get('L1_overrides_of_unanimous', '?')} / {d.get('n_unanimous_L1_cases', '?')} | "
            f"{d.get('L2_overrides_of_unanimous', '?')} / {d.get('n_unanimous_L2_cases', '?')} |"
        )
    lines.append("")

    # --- Synthesis Behavior ---
    lines.append("## 4b. Synthesis Behavior Analysis")
    lines.append("")
    lines.append("**Question:** How does each arbitrator approach synthesis vs. single-rater selection?")
    lines.append("")
    sd = metrics.get('synthesis_detection', {})
    lines.append("| Arbitrator | n | Unanimous N | Unan Synth % | Split N | Split Synth % | Pattern | F1 |")
    lines.append("|------------|---|-------------|--------------|---------|---------------|---------|-----|")
    for arb_name in ARBITRATORS:
        d = sd.get(arb_name, {})
        if not d:
            continue
        unan = d.get('synthesis_when_unanimous', {})
        split = d.get('synthesis_when_split', {})
        lines.append(
            f"| {arb_name} | {d.get('n_pairs', '?'):,} | {unan.get('n', '?'):,} | "
            f"{unan.get('rate_pct', 'N/A') if unan.get('rate_pct') is not None else 'N/A'}% | "
            f"{split.get('n', '?'):,} | {split.get('rate_pct', 'N/A') if split.get('rate_pct') is not None else 'N/A'}% | "
            f"{d.get('interpretation', '?')} | {d.get('f1', '?'):.3f} |"
        )
    lines.append("")
    lines.append("**Pattern Interpretation:**")
    lines.append("- *efficient*: Synthesizes only when raters disagree (ideal)")
    lines.append("- *always_synthesizes*: Synthesizes regardless of rater agreement")
    lines.append("- *deferential*: Rarely synthesizes, prefers to pick a rater")
    lines.append("- *backwards*: Synthesizes more when raters agree than disagree (problematic)")
    lines.append("- *moderate*: No strong pattern")
    lines.append("")

    # --- Bias Analysis ---
    lines.append("## 5. Bias Analysis")
    lines.append("")

    # Position bias
    lines.append("### Position Bias")
    lines.append("")
    pb = metrics.get('position_bias', {})
    for arb_name in ARBITRATORS:
        d = pb.get(arb_name, {})
        if not d:
            continue
        lines.append(f"**{arb_name}** (n={d.get('n_total', '?'):,}):")
        pc = d.get('position_counts', {})
        lines.append(f"  - A: {pc.get('A', 0)}, B: {pc.get('B', 0)}, C: {pc.get('C', 0)}, "
                     f"synthesis: {pc.get('synthesis', 0)} ({d.get('synthesis_rate', '?')}%)")
        chi = d.get('chi_square_test')
        if chi:
            sig = "YES" if chi['significant_at_05'] else "no"
            lines.append(f"  - χ²={chi['chi_square']}, p={chi['p_value']}, "
                         f"significant: {sig}")
        lines.append("")

    # Family bias
    lines.append("### Family Bias (Same-Vendor Preference)")
    lines.append("")
    fb = metrics.get('family_bias', {})
    lines.append("| Arbitrator | Same-Family Rate | Expected | χ² | p | Significant |")
    lines.append("|------------|------------------|----------|----|----|-------------|")
    for arb_name in ARBITRATORS:
        d = fb.get(arb_name, {})
        if not d or d.get('n_non_synthesis', 0) == 0:
            continue
        sig = "YES" if d.get('significant_at_05') else "no"
        lines.append(
            f"| {arb_name} | {d.get('same_family_rate_pct', '?')}% | "
            f"{d.get('expected_rate_pct', '?')}% | "
            f"{d.get('chi_square', '?')} | {d.get('p_value', '?')} | {sig} |"
        )
    lines.append("")

    # --- Barriers by Survey ---
    lines.append("## 6. Barriers by Survey")
    lines.append("")
    bss = metrics.get('barrier_summary_by_survey', {})
    for survey, data in bss.items():
        lines.append(f"### {survey} (n={data.get('n_pairs', '?'):,})")
        lines.append("")

        # L1 distribution
        lines.append("**L1 Barrier Distribution:**")
        lines.append("")
        lines.append("| L1 Code | Count | % |")
        lines.append("|---------|-------|---|")
        l1d = data.get('L1_distribution', {})
        l1p = data.get('L1_percentages', {})
        for code in sorted(l1d.keys(), key=lambda c: -l1d[c]):
            lines.append(f"| {code} | {l1d[code]:,} | {l1p.get(code, '?')}% |")
        lines.append("")

        # Feasibility
        lines.append("**Feasibility:**")
        lines.append("")
        fd = data.get('feasibility_distribution', {})
        fp = data.get('feasibility_percentages', {})
        for f_level in ['F1', 'F2', 'F3']:
            if f_level in fd:
                lines.append(f"- {f_level}: {fd[f_level]:,} ({fp.get(f_level, '?')}%)")

        bc = data.get('binary_consolidability', {})
        if bc:
            lines.append(f"- **Consolidable (F1+F2):** {bc.get('Consolidable', 0):,}")
            lines.append(f"- **Not Consolidable (F3):** {bc.get('Not_Consolidable', 0):,}")
        lines.append("")

        # Top L2
        top = data.get('top_L2_barriers', {})
        if top:
            lines.append("**Top 5 Specific Barriers:**")
            lines.append("")
            for code, count in top.items():
                lines.append(f"- {code}: {count:,}")
            lines.append("")

    # --- Final Verdicts ---
    lines.append("## 7. Final Verdicts")
    lines.append("")
    lines.append("**Confidence Distribution:**")
    lines.append("")
    for level in ['HIGH', 'MODERATE', 'LOW']:
        count = conf.get(level, 0)
        total = sum(conf.values()) if conf else 1
        pct = round(count / total * 100, 1) if total > 0 else 0
        lines.append(f"- {level}: {count:,} ({pct}%)")
    lines.append("")
    lines.append(f"**Unanimous rate (OA+AN agree on both):** {fvs.get('unanimous_rate', '?')}%")
    lines.append(f"**Two-way partial agreement rate (L1 or feas):** {fvs.get('two_way_agreement_rate', '?')}%")
    lines.append(f"**Three-way coverage:** {fvs.get('three_way_coverage', '?')}%")
    lines.append("")
    lines.append("**Tiebreaker rule:** OpenAI arbitrator verdict used when OA and AN disagree "
                 "(two-way); majority vote when three-way data available.")
    lines.append("")

    # --- Limitations ---
    lines.append("## 8. Limitations")
    lines.append("")
    lines.append("- Google arbitrator data is incomplete "
                 f"({meta.get('google_count', '?')}/{meta.get('openai_count', '?')} pairs, "
                 "CPS only).")
    lines.append("- Three-way analysis is CPS-only. FoodAPS has only two-way arbitration.")
    lines.append("- OpenAI used as tiebreaker for two-way disagreements (arbitrary choice, "
                 "documented for transparency).")
    lines.append("")
    lines.append("---")
    lines.append("*Report generated from `stage3_arbitration_metrics.json`*")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"Saved report: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base_dir = REPO_ROOT  # post-restructure: use repo root  # scripts/ -> project root
    analysis_dir = base_dir / "output" / "report_03" / "analysis"

    print("=" * 60)
    print("Stage 3 Arbitration Analysis")
    print("=" * 60)

    # Step 1: Load and validate
    print("\nStep 1: Loading data...")
    arb, raters = load_arbitration_data(base_dir)
    checks = validate_data(arb, raters)
    print(f"  Validation: {json.dumps(checks, indent=2)}")

    # Step 2: Two-way agreement
    print("\nStep 2: Two-way agreement (OA vs AN)...")
    two_way = compute_two_way_agreement(arb)
    print(f"  L1: {two_way.get('L1', {}).get('percent_agreement', '?')}% "
          f"(κ={two_way.get('L1', {}).get('cohens_kappa', '?')})")
    print(f"  Feasibility: {two_way.get('feasibility', {}).get('percent_agreement', '?')}% "
          f"(κ={two_way.get('feasibility', {}).get('cohens_kappa', '?')})")

    # Step 3: Three-way agreement
    print("\nStep 3: Three-way agreement (CPS subset)...")
    three_way = compute_three_way_agreement(arb)
    if 'L1' in three_way:
        print(f"  n={three_way['n_pairs']} pairs")
        print(f"  L1 Fleiss' κ={three_way['L1']['fleiss_kappa']}")
    else:
        print(f"  {three_way.get('error', 'Unknown error')}")

    # Step 4: Arbitrator-rater concordance
    print("\nStep 4: Arbitrator-rater concordance...")
    concordance = compute_arbitrator_rater_concordance(arb, raters)
    for name, data in concordance.items():
        print(f"  {name}: L1 majority concordance = "
              f"{data.get('L1_concordance_with_majority_pct', '?')}%")

    # Step 4b: Synthesis detection
    print("\nStep 4b: Synthesis detection accuracy...")
    synthesis_detection = compute_synthesis_detection(arb, raters)
    for name, data in synthesis_detection.items():
        unan = data['synthesis_when_unanimous']
        split = data['synthesis_when_split']
        print(f"  {name}: P={data['precision']}, R={data['recall']}, F1={data['f1']}, "
              f"pattern={data['interpretation']} "
              f"(unan={unan['rate_pct']}%, split={split['rate_pct']}%)")

    # Step 5: Bias detection
    print("\nStep 5: Bias detection...")
    position_bias = analyze_position_bias(arb)
    family_bias = analyze_family_bias(arb)
    for name in ARBITRATORS:
        pb = position_bias.get(name, {})
        fb = family_bias.get(name, {})
        print(f"  {name}: synthesis rate={pb.get('synthesis_rate', '?')}%, "
              f"same-family={fb.get('same_family_rate_pct', '?')}%")

    # Validate synthesis rate consistency
    validate_synthesis_consistency(synthesis_detection, position_bias)

    # Step 7: Final verdicts (before step 6, needed for survey breakdown)
    print("\nStep 7: Constructing final verdicts...")
    verdicts_df = construct_final_verdicts(arb)
    confidence_dist = verdicts_df['confidence'].value_counts().to_dict()
    print(f"  Confidence: {confidence_dist}")

    # Step 6: By-survey barrier breakdown
    print("\nStep 6: By-survey barrier breakdown...")
    survey_summary = barrier_summary_by_survey(verdicts_df)
    for survey, data in survey_summary.items():
        print(f"  {survey}: {data['n_pairs']} pairs")

    # Confusion matrices
    print("\nGenerating confusion matrices...")
    cm_dir = analysis_dir / 'confusion_matrices'
    cm_files = compute_confusion_matrices(arb, cm_dir)
    print(f"  Saved {len(cm_files)} confusion matrix files")

    # Save final_verdicts.csv
    verdict_cols = [
        'pair_id', 'survey', 'final_L1', 'final_barrier_code', 'final_feasibility',
        'confidence', 'L1_agree_oa_an', 'feas_agree_oa_an', 'has_google',
        'final_barrier_code_oa', 'final_feasibility_oa', 'L1_oa',
        'final_barrier_code_an', 'final_feasibility_an', 'L1_an'
    ]
    # Add google columns if present
    if 'final_barrier_code_go' in verdicts_df.columns:
        verdict_cols.extend(['final_barrier_code_go', 'final_feasibility_go', 'L1_go'])

    verdicts_out = verdicts_df[[c for c in verdict_cols if c in verdicts_df.columns]].copy()
    verdicts_path = analysis_dir / 'final_verdicts.csv'
    verdicts_out.to_csv(verdicts_path, index=False)
    print(f"\nSaved: {verdicts_path}")

    # Save barrier_summary_by_survey.csv
    survey_rows = []
    for survey, data in survey_summary.items():
        for l1_code, count in data['L1_distribution'].items():
            pct = data['L1_percentages'].get(l1_code, 0)
            survey_rows.append({
                'survey': survey,
                'L1_code': l1_code,
                'count': count,
                'pct': pct
            })
    survey_csv = pd.DataFrame(survey_rows)
    survey_csv_path = analysis_dir / 'barrier_summary_by_survey.csv'
    survey_csv.to_csv(survey_csv_path, index=False)
    print(f"Saved: {survey_csv_path}")

    # Compute verdict rates (Task 3)
    total_verdicts = len(verdicts_df)
    unanimous_count = int((verdicts_df['L1_agree_oa_an'] & verdicts_df['feas_agree_oa_an']).sum())

    if 'L1_go' in verdicts_df.columns:
        three_way_mask = verdicts_df['has_google']
        three_way_unanimous = int((
            verdicts_df.loc[three_way_mask, 'L1_agree_oa_an'] &
            verdicts_df.loc[three_way_mask, 'feas_agree_oa_an'] &
            (verdicts_df.loc[three_way_mask, 'L1_oa'] == verdicts_df.loc[three_way_mask, 'L1_go']) &
            (verdicts_df.loc[three_way_mask, 'final_feasibility_oa'] == verdicts_df.loc[three_way_mask, 'final_feasibility_go'])
        ).sum())
    else:
        three_way_unanimous = 0

    # Assemble metrics artifact
    metrics = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "spec_version": "SPEC-R03-S3-001 v1.0",
            "script": "scripts/04_stage3_arbitration.py",
            "two_way_n": len(arb.get('openai', [])),
            "three_way_n": len(arb.get('google', [])),
            "openai_count": len(arb.get('openai', [])),
            "anthropic_count": len(arb.get('anthropic', [])),
            "google_count": len(arb.get('google', [])),
            "google_limitation": "CPS only, rate-limited at 250/day",
            "tiebreaker": "OpenAI arbitrator used for two-way disagreements"
        },
        "validation_checks": checks,
        "two_way_agreement": two_way,
        "three_way_agreement": three_way,
        "arbitrator_rater_concordance": concordance,
        "synthesis_detection": synthesis_detection,
        "position_bias": position_bias,
        "family_bias": family_bias,
        "barrier_summary_by_survey": survey_summary,
        "final_verdict_summary": {
            "total": total_verdicts,
            "confidence_distribution": {k: int(v) for k, v in confidence_dist.items()},
            "unanimous_rate": round(float(unanimous_count / total_verdicts * 100), 1),
            "two_way_agreement_rate": round(float(
                (verdicts_df['L1_agree_oa_an'] | verdicts_df['feas_agree_oa_an']).sum() / total_verdicts * 100
            ), 1),
            "three_way_coverage": round(float(verdicts_df['has_google'].sum() / total_verdicts * 100), 1)
        }
    }

    metrics_path = analysis_dir / 'stage3_arbitration_metrics.json'
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"Saved: {metrics_path}")

    # Generate report
    report_path = analysis_dir / 'stage3_arbitration_report.md'
    generate_report(metrics, report_path)

    print("\n" + "=" * 60)
    print("Stage 3 Arbitration Analysis Complete")
    print("=" * 60)


if __name__ == '__main__':
    main()
