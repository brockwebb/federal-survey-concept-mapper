#!/usr/bin/env python3
"""
05_deliverables_pipeline.py - Scoring, Triage, and Expert Review Deliverables

Part of Report 03: Harmonization Constraints
Stage 5 (Deliverables): Produces stakeholder-ready outputs from Stage 4 findings.

Sub-stages:
  5a: Scoring bake-off (4 methods + ensemble)
  5b: Best-match rollup with triage quadrant assignment
  5c: Expert review tables
  5d: Example pairs for presentation materials
  5e: Sync visuals to presentation
  5f: Model validation visualizations and narratives
  5g: Render slides to PDF

Requires Stage 4 outputs (04_findings_pipeline.py) to exist.

Usage:
    python 05_deliverables_pipeline.py              # Run all sub-stages
    python 05_deliverables_pipeline.py --stage 5a   # Scoring only
    python 05_deliverables_pipeline.py --stage 5b   # Best-match only
    python 05_deliverables_pipeline.py --stage 5c   # Expert tables only
    python 05_deliverables_pipeline.py --stage 5d   # Example pairs only
    python 05_deliverables_pipeline.py --stage 5e   # Sync visuals only
    python 05_deliverables_pipeline.py --stage 5f   # Model validation visuals only
    python 05_deliverables_pipeline.py --stage 5g   # Render slides to PDF
    python 05_deliverables_pipeline.py --dry-run    # Show plan without running
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
SCRIPTS_DIR = BASE_DIR / "scripts"
OUTPUT_DIR = BASE_DIR / "output" / "analysis"
VISUALS_DIR = BASE_DIR / "output" / "visuals"
PRESENTATION_DIR = BASE_DIR / "presentation"
PRESENTATION_IMAGES = PRESENTATION_DIR / "images"

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
    '5d': {
        'name': 'Example Pairs for Presentation',
        'script': 'extract_example_pairs.py',
        'description': 'Extract compelling examples for slide deck',
        'outputs': [
            'example_pairs_for_presentation.md',
            'example_pairs_candidates.csv',
            'example_pairs_README.md',
        ],
        'requires': ['stage4_question_best_matches.csv', 'arbitration_merged.csv'],
    },
    '5e': {
        'name': 'Sync Visuals to Presentation',
        'script': None,  # Built-in function
        'description': 'Copy visuals to presentation/images/ for self-contained deck',
        'outputs': [],  # Presentation images (outside output/analysis/)
        'requires': [],  # Visuals should exist but not blocking
    },
    '5f': {
        'name': 'Model Validation Visualizations',
        'script': 'stage4_model_validation_visuals.py',
        'description': 'Generate model validation heatmaps, charts, and narratives',
        'outputs': [
            'stage4_construct_validity.md',
            'stage4_cost_quality_summary.md',
        ],
        'requires': ['stage2_agreement_metrics.json', 'stage3_arbitration_metrics.json'],
    },
    '5g': {
        'name': 'Render Slides to PDF',
        'script': None,  # Built-in function
        'description': 'Export slide deck to PDF for GitHub distribution',
        'outputs': [],  # slides.pdf in presentation/ (outside output/analysis/)
        'requires': [],  # Slides should exist but not blocking
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


def sync_visuals_to_presentation():
    """Copy visuals from output/visuals/ to presentation/images/."""
    print(f"\n  Syncing visuals to presentation...")

    # Create presentation images directory if it doesn't exist
    PRESENTATION_IMAGES.mkdir(parents=True, exist_ok=True)

    # Check if visuals directory exists
    if not VISUALS_DIR.exists():
        print(f"  WARNING: Visuals directory not found: {VISUALS_DIR}")
        print(f"  Skipping visual sync. Run visualization generation first.")
        return True

    # Copy all PNG files
    png_files = list(VISUALS_DIR.glob("*.png"))
    if not png_files:
        print(f"  WARNING: No PNG files found in {VISUALS_DIR}")
        return True

    copied = 0
    for src in png_files:
        dst = PRESENTATION_IMAGES / src.name
        shutil.copy2(src, dst)
        size_kb = dst.stat().st_size / 1024
        print(f"  ✓ {src.name} ({size_kb:.1f}KB)")
        copied += 1

    print(f"\n  Synced {copied} visual(s) to {PRESENTATION_IMAGES}")
    print(f"  Presentation is now self-contained with latest visuals.")
    return True


def render_slides_pdf():
    """Render slide decks to PDF for GitHub distribution."""
    print(f"\n  Rendering slides to PDF...")

    decks = [
        "slides_3a_findings.qmd",
        "slides_3b_methodology.qmd",
        "slides.qmd"  # Keep original for backup
    ]

    success_count = 0
    for deck_name in decks:
        slides_qmd = PRESENTATION_DIR / deck_name

        if not slides_qmd.exists():
            print(f"  WARNING: Slides not found: {deck_name}")
            continue

        try:
            print(f"  Rendering {deck_name}...")
            result = subprocess.run(
                ["quarto", "render", str(slides_qmd), "--to", "beamer"],
                capture_output=True,
                text=True,
                cwd=str(PRESENTATION_DIR)
            )

            if result.returncode != 0:
                print(f"  ERROR: Quarto PDF render failed for {deck_name}")
                print(f"  {result.stderr}")
                continue

            # Quarto puts PDF in _output/ directory
            pdf_name = deck_name.replace('.qmd', '.pdf')
            pdf_output = PRESENTATION_DIR / "_output" / pdf_name
            pdf_dest = PRESENTATION_DIR / pdf_name

            if pdf_output.exists():
                # Copy to presentation root for easier access
                shutil.copy2(pdf_output, pdf_dest)
                size_mb = pdf_dest.stat().st_size / (1024 * 1024)
                print(f"  ✓ PDF created: {pdf_name} ({size_mb:.1f}MB)")
                success_count += 1
            else:
                print(f"  WARNING: PDF not found after render for {deck_name}")

        except FileNotFoundError:
            print(f"  ERROR: Quarto not found. Install with: brew install quarto")
            print(f"  Or skip PDF generation — HTML slides work fine.")
            return False

    if success_count == 0:
        print(f"  ERROR: No slide decks were successfully rendered")
        return False

    print(f"  ✓ Successfully rendered {success_count}/{len(decks)} slide decks")
    return True


def run_stage(stage_key, dry_run=False):
    """Run a single sub-stage."""
    stage = STAGES[stage_key]

    print(f"\n{'=' * 60}")
    print(f"STAGE {stage_key.upper()}: {stage['name']}")
    print(f"  {stage['description']}")

    # Special handling for built-in functions (5e, 5g)
    if stage_key == '5e':
        print(f"  Action: Built-in function")
        print(f"{'=' * 60}")

        if dry_run:
            print(f"\n  [DRY RUN] Would sync visuals from {VISUALS_DIR}")
            print(f"  Target: {PRESENTATION_IMAGES}")
            png_files = list(VISUALS_DIR.glob("*.png")) if VISUALS_DIR.exists() else []
            print(f"  Files to copy: {len(png_files)}")
            for f in png_files:
                print(f"    - {f.name}")
            return True

        # Run visual sync
        success = sync_visuals_to_presentation()
        if success:
            print(f"\n  [OK] {stage['name']} complete.")
        return success

    if stage_key == '5g':
        print(f"  Action: Built-in function")
        print(f"{'=' * 60}")

        if dry_run:
            slides_qmd = PRESENTATION_DIR / "slides.qmd"
            print(f"\n  [DRY RUN] Would render: {slides_qmd}")
            print(f"  Output: {PRESENTATION_DIR / 'slides.pdf'}")
            print(f"  Command: quarto render slides.qmd --to beamer")
            return True

        # Run PDF render
        success = render_slides_pdf()
        if success:
            print(f"\n  [OK] {stage['name']} complete.")
        return success

    # Standard script-based stage
    script_path = SCRIPTS_DIR / stage['script']
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
  5d  Example pairs for presentation
  5e  Sync visuals to presentation
  5f  Model validation visualizations and narratives
  5g  Render slides to PDF

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
