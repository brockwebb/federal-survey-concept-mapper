#!/usr/bin/env python3
"""
03_analysis_pipeline.py - Post-arbitration analysis pipeline

Part of Report 03: Harmonization Constraints
Stages: 4 (Cleanup), 5 (Agreement Analysis), 6 (Descriptive Stats)

Orchestrates:
  - scripts/clean_arbitration_data.py
  - scripts/analyze_arbitration_agreement.py
  - scripts/descriptive_stats.py

Usage:
    python 03_analysis_pipeline.py              # Run all stages
    python 03_analysis_pipeline.py --stage 4    # Run specific stage
    python 03_analysis_pipeline.py --stage 4-5  # Run stage range
"""

import argparse
import subprocess
import sys
from pathlib import Path


# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
SCRIPTS_DIR = SRC_DIR / "scripts"


STAGES = {
    4: {
        'name': 'Arbitration Cleanup',
        'script': 'clean_arbitration_data.py',
        'args': []
    },
    5: {
        'name': 'Agreement Analysis',
        'script': 'analyze_arbitration_agreement.py',
        'args': []
    },
    6: {
        'name': 'Descriptive Statistics',
        'script': 'descriptive_stats.py',
        'args': ['--stage', 'all']
    }
}


def run_stage(stage_num):
    """Run a single pipeline stage."""
    if stage_num not in STAGES:
        print(f"ERROR: Unknown stage {stage_num}")
        return False

    stage = STAGES[stage_num]
    script_path = SCRIPTS_DIR / stage['script']

    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        return False

    print(f"\n{'=' * 60}")
    print(f"STAGE {stage_num}: {stage['name']}")
    print(f"Script: {stage['script']}")
    print('=' * 60)

    cmd = [sys.executable, str(script_path)] + stage['args']
    result = subprocess.run(cmd, cwd=REPO_ROOT)

    if result.returncode != 0:
        print(f"ERROR: Stage {stage_num} failed with code {result.returncode}")
        return False

    return True


def parse_stage_range(stage_arg):
    """Parse stage argument like '4', '4-5', or None (all)."""
    if stage_arg is None:
        return list(STAGES.keys())

    if '-' in stage_arg:
        start, end = stage_arg.split('-')
        return list(range(int(start), int(end) + 1))

    return [int(stage_arg)]


def main():
    parser = argparse.ArgumentParser(description='Run post-arbitration analysis pipeline')
    parser.add_argument('--stage', type=str, default=None,
                       help='Stage to run: 4, 5, 6, or range like 4-5 (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would run without executing')
    args = parser.parse_args()

    stages_to_run = parse_stage_range(args.stage)

    print("Post-Arbitration Analysis Pipeline")
    print(f"Stages to run: {stages_to_run}")

    if args.dry_run:
        print("\n[DRY RUN - not executing]")
        for stage_num in stages_to_run:
            stage = STAGES.get(stage_num, {})
            print(f"  Stage {stage_num}: {stage.get('name', 'Unknown')} -> {stage.get('script', 'N/A')}")
        return

    for stage_num in stages_to_run:
        success = run_stage(stage_num)
        if not success:
            print(f"\nPipeline halted at stage {stage_num}")
            sys.exit(1)

    print(f"\n{'=' * 60}")
    print("Pipeline complete.")
    print('=' * 60)


if __name__ == "__main__":
    main()
