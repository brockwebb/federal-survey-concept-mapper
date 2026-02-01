#!/usr/bin/env python3
"""
05_deliverables_pipeline.py - Scoring, Triage, and Expert Review Deliverables

Part of Report 03: Harmonization Constraints
Stage 5 (Deliverables): Produces stakeholder-ready outputs from Stage 4 findings.

Sub-stages:
  5a: Scoring bake-off (4 methods + ensemble)
  5b: Best-match rollup with triage quadrant assignment
  5c: Expert review tables

Requires Stage 4 outputs (04_findings_pipeline.py) to exist.

Usage:
    python 05_deliverables_pipeline.py              # Run all sub-stages
    python 05_deliverables_pipeline.py --stage 5a   # Scoring only
    python 05_deliverables_pipeline.py --stage 5b   # Best-match only
    python 05_deliverables_pipeline.py --stage 5c   # Expert tables only
    python 05_deliverables_pipeline.py --dry-run    # Show plan without running
"""

import argparse
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output" / "analysis"

STAGES = {
    '5a': {
        'name': 'Scoring Bake-Off',
        'script': 'stage4_scoring_bakeoff.py',
        'description': '4-method scoring comparison + ensemble',
        'outputs': [
            'stage4_bakeoff_scores.csv',
            'stage4_bakeoff_correlations.csv',
            'stage4_bakeoff_report.md',
            'stage4_divergent_pairs.csv',
            'stage4_score_distributions.json',
        ],
        'requires': ['final_verdicts.csv', 'barrier_coding_merged_3rater.csv'],
    },
    '5b': {
        'name': 'Best-Match Rollup',
        'script': 'stage4_best_match_rollup.py',
        'description': 'Best ACS match per question + triage quadrant',
        'outputs': [
            'stage4_question_best_matches.csv',
        ],
        'requires': ['stage4_bakeoff_scores.csv', 'stage4_question_level.csv', 'final_verdicts.csv'],
    },
    '5c': {
        'name': 'Expert Review Tables',
        'script': 'build_expert_review_table.py',
        'description': 'Stakeholder-ready review tables with reasoning',
        'outputs': [
            'expert_review_cps.csv',
            'expert_review_foodaps.csv',
            'expert_review_combined.csv',
            'taxonomy_reference.md',
            'classification_distribution.md',
        ],
        'requires': ['stage4_question_best_matches.csv', 'final_verdicts.csv', 'arbitration_merged.csv'],
    },
}


def check_prerequisites(stage_key):
    """Check that required input files exist."""
    stage = STAGES[stage_key]
    missing = []
    for req in stage['requires']:
        if not (OUTPUT_DIR / req).exists():
            missing.append(req)
    return missing


def run_stage(stage_key, dry_run=False):
    """Run a single sub-stage."""
    stage = STAGES[stage_key]
    script_path = SCRIPTS_DIR / stage['script']

    print(f"\n{'=' * 60}")
    print(f"STAGE {stage_key.upper()}: {stage['name']}")
    print(f"  {stage['description']}")
    print(f"  Script: {script_path.name}")
    print(f"{'=' * 60}")

    # Check prerequisites
    missing = check_prerequisites(stage_key)
    if missing:
        print(f"\n  ERROR: Missing prerequisites:")
        for m in missing:
            print(f"    - {m}")
        print(f"\n  Run earlier stages first.")
        return False

    if not script_path.exists():
        print(f"\n  ERROR: Script not found: {script_path}")
        return False

    if dry_run:
        print(f"\n  [DRY RUN] Would run: python {script_path}")
        print(f"  Outputs:")
        for out in stage['outputs']:
            exists = (OUTPUT_DIR / out).exists()
            status = "EXISTS" if exists else "PENDING"
            print(f"    [{status}] {out}")
        return True

    print()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=str(BASE_DIR),
    )

    if result.returncode != 0:
        print(f"\n  ERROR: {stage['script']} exited with code {result.returncode}")
        return False

    print(f"\n  [OK] {stage['name']} complete.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Stage 5: Deliverables Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Sub-stages:
  5a  Scoring bake-off (4 methods + ensemble)
  5b  Best-match rollup with triage quadrants
  5c  Expert review tables

Examples:
  python 05_deliverables_pipeline.py              # Run all
  python 05_deliverables_pipeline.py --stage 5b   # Just best-match
  python 05_deliverables_pipeline.py --dry-run    # Show plan
        """
    )

    parser.add_argument(
        '--stage', '-s',
        choices=list(STAGES.keys()) + ['all'],
        default='all',
        help='Sub-stage to run (default: all)'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show execution plan without running'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("DELIVERABLES PIPELINE (Stage 5)")
    print("=" * 60)

    if args.dry_run:
        print("[DRY RUN MODE]")

    stages_to_run = list(STAGES.keys()) if args.stage == 'all' else [args.stage]

    success = True
    for stage_key in stages_to_run:
        if not run_stage(stage_key, args.dry_run):
            success = False
            if not args.dry_run:
                print(f"\nPipeline stopped at stage {stage_key}.")
                sys.exit(1)

    print(f"\n{'=' * 60}")
    if success:
        print("DELIVERABLES PIPELINE COMPLETE")
    else:
        print("DELIVERABLES PIPELINE INCOMPLETE (see errors above)")
    print(f"{'=' * 60}")

    if not args.dry_run and success:
        print(f"\nOutputs in: {OUTPUT_DIR}/")


if __name__ == '__main__':
    main()
