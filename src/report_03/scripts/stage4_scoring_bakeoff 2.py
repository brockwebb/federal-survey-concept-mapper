#!/usr/bin/env python3
"""
stage4_scoring_bakeoff.py - Compare 4 scoring methods for consolidability ranking

Implements:
  1. Composite Score (weighted product of feasibility × confidence)
  2. Entropy-Based Confidence (Shannon entropy of vote distribution)
  3. Bayesian Posterior (Beta-Binomial model)
  4. Borda Count (rank aggregation)

Plus an ensemble of all four and correlation/divergence analysis.

Usage:
    python scripts/stage4_scoring_bakeoff.py
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from collections import Counter

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from lib.io_utils import ensure_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "output" / "analysis"

FEAS_LEVELS = ['F1', 'F2', 'F3']
METHODS = ['composite', 'entropy', 'bayesian', 'borda']


# ---------------------------------------------------------------------------
# Scoring Methods
# ---------------------------------------------------------------------------

def composite_score(feasibility, confidence):
    """Method 1: Weighted product of feasibility and confidence.
    Range: 0.33 (F3+LOW) to 3.0 (F1+HIGH).
    """
    feas_map = {'F1': 3, 'F2': 2, 'F3': 1}
    conf_map = {'HIGH': 1.0, 'MODERATE': 0.67, 'LOW': 0.33}
    return feas_map.get(feasibility, 0) * conf_map.get(confidence, 0.5)


def entropy_score(votes):
    """Shannon entropy of vote distribution, inverted so 1 = perfect agreement."""
    if not votes:
        return 0.0
    counts = Counter(votes)
    n = len(votes)
    probs = [c / n for c in counts.values()]
    H = -sum(p * np.log2(p) for p in probs if p > 0)
    H_max = np.log2(3)  # max entropy for 3 feasibility categories
    return 1 - (H / H_max)


def entropy_composite(votes, final_feasibility):
    """Method 2: Entropy agreement weighted by feasibility direction."""
    agreement = entropy_score(votes)
    feas_weight = {'F1': 1.0, 'F2': 0.67, 'F3': 0.33}
    return agreement * feas_weight.get(final_feasibility, 0.33)


def bayesian_score(votes, prior_rate=0.197):
    """Method 3: Posterior P(consolidable | votes) via Beta-Binomial.
    prior_rate calibrated from observed pair-level base rate.
    """
    successes = sum(1 for v in votes if v in ('F1', 'F2'))
    failures = len(votes) - successes

    # Weak prior: α+β=2, mean=prior_rate
    alpha_prior = prior_rate * 2
    beta_prior = (1 - prior_rate) * 2

    alpha_post = alpha_prior + successes
    beta_post = beta_prior + failures
    return alpha_post / (alpha_post + beta_post)


def borda_score(votes):
    """Method 4: Borda count. F1=2, F2=1, F3=0. Normalized to [0,1]."""
    if not votes:
        return 0.0
    points = {'F1': 2, 'F2': 1, 'F3': 0}
    total = sum(points.get(v, 0) for v in votes)
    max_possible = 2 * len(votes)
    return total / max_possible if max_possible > 0 else 0.0


# ---------------------------------------------------------------------------
# Data Preparation
# ---------------------------------------------------------------------------

def load_and_prepare():
    """Load verdicts + rater data, build vote matrix."""
    verdicts = pd.read_csv(OUTPUT_DIR / "final_verdicts.csv")
    log.info(f"Loaded {len(verdicts)} verdict rows")

    # Load rater-level feasibility
    raters = pd.read_csv(OUTPUT_DIR / "barrier_coding_merged_3rater.csv")
    raters = raters[['pair_id', 'feasibility_openai', 'feasibility_anthropic', 'feasibility_google']]
    raters.columns = ['pair_id', 'rater_feas_oa', 'rater_feas_an', 'rater_feas_go']

    df = verdicts.merge(raters, on='pair_id', how='left')

    # Build vote lists
    all_votes = []
    arb_votes = []
    for _, row in df.iterrows():
        # Arbitrator votes
        arb = [row['final_feasibility_oa'], row['final_feasibility_an']]
        if row['has_google'] and pd.notna(row.get('final_feasibility_go')):
            arb.append(row['final_feasibility_go'])
        arb = [v for v in arb if v in FEAS_LEVELS]

        # Rater votes
        rater = []
        for col in ['rater_feas_oa', 'rater_feas_an', 'rater_feas_go']:
            v = row.get(col)
            if pd.notna(v) and v in FEAS_LEVELS:
                rater.append(v)

        arb_votes.append(arb)
        all_votes.append(rater + arb)

    df['arb_votes'] = arb_votes
    df['all_votes'] = all_votes
    df['n_arb_votes'] = df['arb_votes'].apply(len)
    df['n_all_votes'] = df['all_votes'].apply(len)

    log.info(f"Vote counts — arb: {df['n_arb_votes'].value_counts().to_dict()}, "
             f"all: {df['n_all_votes'].value_counts().to_dict()}")

    return df


# ---------------------------------------------------------------------------
# Scoring Pipeline
# ---------------------------------------------------------------------------

def compute_scores(df):
    """Compute all 4 method scores using the full vote set (raters + arbitrators)."""

    # Method 1: Composite (uses final verdict + confidence, not individual votes)
    df['score_composite'] = df.apply(
        lambda r: composite_score(r['final_feasibility'], r['confidence']), axis=1)

    # Methods 2-4: Use all available votes
    df['score_entropy'] = df.apply(
        lambda r: entropy_composite(r['all_votes'], r['final_feasibility']), axis=1)
    df['score_bayesian'] = df['all_votes'].apply(bayesian_score)
    df['score_borda'] = df['all_votes'].apply(borda_score)

    # Ranks (higher score = better rank = lower rank number)
    for method in METHODS:
        df[f'rank_{method}'] = df[f'score_{method}'].rank(ascending=False, method='min')

    # Ensemble: mean of min-max normalized scores
    for method in METHODS:
        col = f'score_{method}'
        mn, mx = df[col].min(), df[col].max()
        if mx > mn:
            df[f'score_{method}_norm'] = (df[col] - mn) / (mx - mn)
        else:
            df[f'score_{method}_norm'] = 0.5

    df['score_ensemble'] = df[[f'score_{m}_norm' for m in METHODS]].mean(axis=1)
    df['rank_ensemble'] = df['score_ensemble'].rank(ascending=False, method='min')

    return df


# ---------------------------------------------------------------------------
# Correlation Analysis
# ---------------------------------------------------------------------------

def compute_correlations(df):
    """Spearman rank correlations between all method pairs."""
    all_methods = METHODS + ['ensemble']
    n = len(all_methods)
    corr_matrix = pd.DataFrame(np.ones((n, n)), index=all_methods, columns=all_methods)
    pval_matrix = pd.DataFrame(np.zeros((n, n)), index=all_methods, columns=all_methods)

    for i, m1 in enumerate(all_methods):
        for j, m2 in enumerate(all_methods):
            if i < j:
                rho, pval = spearmanr(df[f'score_{m1}'], df[f'score_{m2}'])
                corr_matrix.loc[m1, m2] = round(rho, 4)
                corr_matrix.loc[m2, m1] = round(rho, 4)
                pval_matrix.loc[m1, m2] = pval
                pval_matrix.loc[m2, m1] = pval

    return corr_matrix, pval_matrix


# ---------------------------------------------------------------------------
# Divergence Analysis
# ---------------------------------------------------------------------------

def find_divergent_pairs(df, n=20):
    """Find pairs where methods disagree most on ranking."""
    rank_cols = [f'rank_{m}' for m in METHODS]
    df['rank_std'] = df[rank_cols].std(axis=1)
    divergent = df.nlargest(n, 'rank_std')
    return divergent


# ---------------------------------------------------------------------------
# Score Distributions
# ---------------------------------------------------------------------------

def compute_distributions(df):
    """Summary statistics for each scoring method."""
    stats = {}
    for method in METHODS + ['ensemble']:
        col = f'score_{method}'
        s = df[col]
        stats[method] = {
            'mean': round(float(s.mean()), 4),
            'std': round(float(s.std()), 4),
            'min': round(float(s.min()), 4),
            'q25': round(float(s.quantile(0.25)), 4),
            'median': round(float(s.median()), 4),
            'q75': round(float(s.quantile(0.75)), 4),
            'max': round(float(s.max()), 4),
        }
        # Distribution by feasibility
        for feas in FEAS_LEVELS:
            subset = df[df['final_feasibility'] == feas][col]
            stats[method][f'{feas}_mean'] = round(float(subset.mean()), 4) if len(subset) > 0 else None
            stats[method][f'{feas}_std'] = round(float(subset.std()), 4) if len(subset) > 0 else None
    return stats


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(df, corr_matrix, divergent, distributions, survey_summary=None):
    """Generate human-readable bakeoff report."""
    lines = []
    now = datetime.now().isoformat()

    lines.append("# Stage 4: Scoring Bake-Off Report")
    lines.append(f"\n**Generated:** {now}")
    lines.append(f"**Pairs scored:** {len(df)}")
    lines.append(f"**Vote sources:** 3 raters + 2–3 arbitrators per pair")
    lines.append("")

    # --- Method Descriptions ---
    lines.append("## Methods")
    lines.append("")
    lines.append("| # | Method | Approach | Inputs |")
    lines.append("|---|--------|----------|--------|")
    lines.append("| 1 | Composite | Feasibility weight × confidence weight | Final verdict + confidence |")
    lines.append("| 2 | Entropy | Inverted Shannon entropy × feasibility weight | All 5–6 votes |")
    lines.append("| 3 | Bayesian | Beta-Binomial posterior P(consolidable) | All 5–6 votes (binary) |")
    lines.append("| 4 | Borda | Normalized point sum (F1=2, F2=1, F3=0) | All 5–6 votes |")
    lines.append("| E | Ensemble | Mean of min-max normalized scores | Methods 1–4 |")
    lines.append("")

    # --- Score Distributions ---
    lines.append("## Score Distributions")
    lines.append("")
    lines.append("| Method | Mean | Std | Min | Q25 | Median | Q75 | Max |")
    lines.append("|--------|-----:|----:|----:|----:|-------:|----:|----:|")
    for method in METHODS + ['ensemble']:
        d = distributions[method]
        lines.append(f"| {method} | {d['mean']:.3f} | {d['std']:.3f} | {d['min']:.3f} "
                     f"| {d['q25']:.3f} | {d['median']:.3f} | {d['q75']:.3f} | {d['max']:.3f} |")
    lines.append("")

    # --- Scores by Feasibility ---
    lines.append("### Mean Score by Final Feasibility")
    lines.append("")
    lines.append("| Method | F1 Mean | F2 Mean | F3 Mean |")
    lines.append("|--------|--------:|--------:|--------:|")
    for method in METHODS + ['ensemble']:
        d = distributions[method]
        f1 = f"{d['F1_mean']:.3f}" if d.get('F1_mean') is not None else "—"
        f2 = f"{d['F2_mean']:.3f}" if d.get('F2_mean') is not None else "—"
        f3 = f"{d['F3_mean']:.3f}" if d.get('F3_mean') is not None else "—"
        lines.append(f"| {method} | {f1} | {f2} | {f3} |")
    lines.append("")

    # --- Correlation Matrix ---
    lines.append("## Spearman Rank Correlations")
    lines.append("")
    all_methods = METHODS + ['ensemble']
    header = "| | " + " | ".join(all_methods) + " |"
    sep = "|---|" + "|".join(["----:" for _ in all_methods]) + "|"
    lines.append(header)
    lines.append(sep)
    for m1 in all_methods:
        vals = " | ".join(f"{corr_matrix.loc[m1, m2]:.3f}" for m2 in all_methods)
        lines.append(f"| {m1} | {vals} |")
    lines.append("")

    # Interpret correlations
    lines.append("### Interpretation")
    lines.append("")
    pairs_high = []
    pairs_low = []
    for i, m1 in enumerate(METHODS):
        for j, m2 in enumerate(METHODS):
            if i < j:
                rho = corr_matrix.loc[m1, m2]
                if rho >= 0.95:
                    pairs_high.append((m1, m2, rho))
                elif rho < 0.85:
                    pairs_low.append((m1, m2, rho))

    if pairs_high:
        lines.append("**Near-redundant pairs** (ρ ≥ 0.95):")
        for m1, m2, rho in pairs_high:
            lines.append(f"- {m1} ↔ {m2}: ρ = {rho:.3f}")
        lines.append("")
    if pairs_low:
        lines.append("**Most divergent pairs** (ρ < 0.85):")
        for m1, m2, rho in pairs_low:
            lines.append(f"- {m1} ↔ {m2}: ρ = {rho:.3f}")
        lines.append("")

    # --- Divergent Pairs ---
    lines.append("## Most Divergent Pairs (Top 20)")
    lines.append("")
    lines.append("Pairs where the 4 methods disagree most on ranking (highest rank std dev):")
    lines.append("")
    lines.append("| pair_id | feas | conf | composite | entropy | bayesian | borda | rank_std |")
    lines.append("|---------|------|------|----------:|--------:|---------:|------:|---------:|")
    for _, row in divergent.head(20).iterrows():
        lines.append(f"| {row['pair_id']} | {row['final_feasibility']} | {row['confidence']} "
                     f"| {row['score_composite']:.2f} | {row['score_entropy']:.3f} "
                     f"| {row['score_bayesian']:.3f} | {row['score_borda']:.3f} "
                     f"| {row['rank_std']:.1f} |")
    lines.append("")

    # --- Recommendation ---
    lines.append("## Recommendation")
    lines.append("")

    # Check separability: do all methods cleanly separate F1/F2 from F3?
    lines.append("### Separability Check")
    lines.append("")
    lines.append("A good scoring method should separate consolidable (F1/F2) from non-consolidable (F3):")
    lines.append("")
    for method in METHODS + ['ensemble']:
        col = f'score_{method}'
        f12_scores = df[df['final_feasibility'].isin(['F1', 'F2'])][col]
        f3_scores = df[df['final_feasibility'] == 'F3'][col]
        overlap = (f12_scores.min() <= f3_scores.max())
        gap = f12_scores.min() - f3_scores.max()
        lines.append(f"- **{method}:** F1/F2 min={f12_scores.min():.3f}, "
                     f"F3 max={f3_scores.max():.3f}, "
                     f"gap={'%.3f' % gap if gap > 0 else 'OVERLAP'}")
    lines.append("")

    lines.append("### Summary")
    lines.append("")
    lines.append("- **Composite** is the simplest and most interpretable for stakeholders")
    lines.append("- **Entropy** and **Borda** leverage full vote distributions")
    lines.append("- **Bayesian** provides a probabilistic interpretation")
    lines.append("- **Ensemble** smooths over method-specific quirks and is recommended "
                 "for final ranking when no single method clearly dominates")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("**Methodology:** Each pair scored by 3 raters (Stage 1) and 2–3 arbitrators "
                 "(Stage 3). Votes converted to feasibility classifications (F1/F2/F3). "
                 "Four scoring methods applied independently, then combined via mean of "
                 "min-max normalized scores.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=== Stage 4: Scoring Bake-Off ===")
    ensure_dir(OUTPUT_DIR)

    # Load data and build vote matrix
    df = load_and_prepare()

    # Compute all scores
    df = compute_scores(df)
    log.info("Scores computed for all 4 methods + ensemble")

    # Correlation analysis
    corr_matrix, pval_matrix = compute_correlations(df)
    log.info("Correlation matrix:")
    for m1 in METHODS:
        vals = ", ".join(f"{m2}={corr_matrix.loc[m1, m2]:.3f}" for m2 in METHODS if m2 != m1)
        log.info(f"  {m1}: {vals}")

    # Divergent pairs
    divergent = find_divergent_pairs(df, n=20)

    # Score distributions
    distributions = compute_distributions(df)

    # --- Write Outputs ---

    # 1. Scores CSV
    score_cols = ['pair_id', 'final_feasibility', 'confidence', 'n_all_votes',
                  'score_composite', 'score_entropy', 'score_bayesian', 'score_borda',
                  'score_ensemble',
                  'rank_composite', 'rank_entropy', 'rank_bayesian', 'rank_borda',
                  'rank_ensemble']
    scores_path = OUTPUT_DIR / "stage4_bakeoff_scores.csv"
    df[score_cols].to_csv(scores_path, index=False)
    log.info(f"Wrote {scores_path}")

    # 2. Correlations CSV
    corr_path = OUTPUT_DIR / "stage4_bakeoff_correlations.csv"
    corr_matrix.to_csv(corr_path)
    log.info(f"Wrote {corr_path}")

    # 3. Report
    report = generate_report(df, corr_matrix, divergent, distributions)
    report_path = OUTPUT_DIR / "stage4_bakeoff_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    log.info(f"Wrote {report_path}")

    # 4. Divergent pairs CSV
    div_cols = score_cols + ['rank_std']
    div_path = OUTPUT_DIR / "stage4_divergent_pairs.csv"
    divergent[div_cols].to_csv(div_path, index=False)
    log.info(f"Wrote {div_path}")

    # 5. Score distributions JSON
    dist_path = OUTPUT_DIR / "stage4_score_distributions.json"
    with open(dist_path, 'w') as f:
        json.dump(distributions, f, indent=2)
    log.info(f"Wrote {dist_path}")

    log.info("=== Scoring bake-off complete ===")


if __name__ == '__main__':
    main()
