#!/usr/bin/env python3
"""
Barrier Coding Pipeline Orchestrator v2.0
Report 03: Harmonization Constraints

Config-driven pipeline for multi-model barrier coding and arbitration.
All model names are defined in config.yaml - no hardcoding.

Usage:
    python run_pipeline.py --stage rate --raters openai,anthropic
    python run_pipeline.py --stage arbitrate --arbitrators anthropic
    python run_pipeline.py --stage all
    python run_pipeline.py --validate-config
    python run_pipeline.py --dry-run
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(Path(__file__).parent.parent.parent / '.env')

VERSION = "2.0"


def load_config(config_path: Path = Path('./config.yaml')) -> Dict:
    """Load pipeline configuration from YAML."""
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path) as f:
        return yaml.safe_load(f)


def check_api_key(env_var: str) -> bool:
    """Check if API key environment variable is set."""
    return bool(os.getenv(env_var))


def print_banner(config: Dict, stage: str, raters: List[str], arbitrators: List[str]):
    """Print startup banner with configuration summary."""
    print("=" * 60)
    print(f"BARRIER CODING PIPELINE v{VERSION}")
    print("=" * 60)
    print(f"Stage: {stage}")
    print()

    if stage in ('rate', 'all'):
        print("RATERS (serial):")
        for i, key in enumerate(raters, 1):
            rater = config['raters'][key]
            api_status = "OK" if check_api_key(rater['api_key_env']) else "MISSING"
            print(f"  [{i}] {key}: {rater['model']} [API: {api_status}]")
        print()

    if stage in ('arbitrate', 'all'):
        print("ARBITRATORS (serial):")
        for i, key in enumerate(arbitrators, 1):
            arb = config['arbitrators'][key]
            api_status = "OK" if check_api_key(arb['api_key_env']) else "MISSING"
            print(f"  [{i}] {key}: {arb['model']} [API: {api_status}]")
        print()

    print("=" * 60)


def validate_config(config: Dict) -> bool:
    """Validate configuration and check API keys."""
    print("\nValidating configuration...")
    print()

    all_ok = True

    # Check raters
    print("RATERS:")
    for key, rater in config['raters'].items():
        api_ok = check_api_key(rater['api_key_env'])
        status = "OK" if api_ok else "MISSING"
        symbol = "[OK]" if api_ok else "[X]"
        temp = rater.get('temperature')
        temp_str = str(temp) if temp is not None else "null (omitted)"
        print(f"  {symbol} {key}: {rater['model']}")
        print(f"       Provider: {rater['provider']}")
        print(f"       Temperature: {temp_str}")
        print(f"       API Key: {rater['api_key_env']} = {status}")
        if not api_ok:
            all_ok = False

    print()

    # Check arbitrators
    print("ARBITRATORS:")
    for key, arb in config['arbitrators'].items():
        api_ok = check_api_key(arb['api_key_env'])
        status = "OK" if api_ok else "MISSING"
        symbol = "[OK]" if api_ok else "[X]"
        temp = arb.get('temperature')
        temp_str = str(temp) if temp is not None else "null (omitted)"
        print(f"  {symbol} {key}: {arb['model']}")
        print(f"       Provider: {arb['provider']}")
        print(f"       Temperature: {temp_str}")
        print(f"       API Key: {arb['api_key_env']} = {status}")
        if not api_ok:
            all_ok = False

    print()

    # Check paths
    print("PATHS:")
    for name, path in config['paths'].items():
        print(f"  {name}: {path}")

    print()

    # Check pipeline settings
    print("PIPELINE SETTINGS:")
    for name, value in config['pipeline'].items():
        print(f"  {name}: {value}")

    print()
    print("=" * 60)

    if all_ok:
        print("Configuration is valid. All API keys present.")
    else:
        print("WARNING: Some API keys are missing.")
        print("Set them in .env file or environment.")

    print("=" * 60)

    return all_ok


def ensure_directories(config: Dict):
    """Create output directories if they don't exist."""
    base = Path(config['paths']['output_dir'])
    subdirs = ['results_subdir', 'analysis_subdir', 'checkpoints_subdir']

    for subdir_key in subdirs:
        path = base / config['paths'][subdir_key]
        path.mkdir(parents=True, exist_ok=True)


def run_stage_banner(provider: str, model: str, current: int, total: int, stage_type: str):
    """Print banner for running a specific model."""
    print()
    print("=" * 60)
    print(f"RUNNING: {provider} - {model}")
    print(f"Progress: {current}/{total} {stage_type} complete")
    print("=" * 60)
    print()


def run_rating_stage(config: Dict, raters: List[str], dry_run: bool = False) -> bool:
    """Run barrier coding rating for specified raters."""
    from importlib.machinery import SourceFileLoader
    _mod = SourceFileLoader("barrier_pipeline", str(Path(__file__).parent / "01_barrier_pipeline.py")).load_module()
    run_single_rater = _mod.run_single_rater

    total = len(raters)

    for i, rater_key in enumerate(raters):
        rater = config['raters'][rater_key]
        run_stage_banner(rater_key, rater['model'], i, total, "raters")

        if dry_run:
            print(f"  [DRY RUN] Would run {rater_key} rater with model {rater['model']}")
            continue

        success = run_single_rater(config, rater_key)

        if not success:
            print(f"\nERROR: Rater {rater_key} failed. Stopping pipeline.")
            return False

        print(f"\n[OK] Rater {rater_key} complete.")

    return True


def run_arbitration_stage(config: Dict, arbitrators: List[str], dry_run: bool = False) -> bool:
    """Run arbitration for specified arbitrators."""
    from importlib.machinery import SourceFileLoader
    _mod = SourceFileLoader("arbitration_pipeline", str(Path(__file__).parent / "02_arbitration_pipeline.py")).load_module()
    run_single_arbitrator = _mod.run_single_arbitrator
    load_disagreements = _mod.load_disagreements

    # Load disagreements (requires rating results)
    if not dry_run:
        disagreements_df = load_disagreements(config)
        if disagreements_df is None or len(disagreements_df) == 0:
            print("ERROR: No disagreements to arbitrate. Run rating stage first.")
            return False
        print(f"Loaded {len(disagreements_df)} disagreements for arbitration.")
    else:
        disagreements_df = None

    total = len(arbitrators)

    for i, arb_key in enumerate(arbitrators):
        arb = config['arbitrators'][arb_key]
        run_stage_banner(arb_key, arb['model'], i, total, "arbitrators")

        if dry_run:
            print(f"  [DRY RUN] Would run {arb_key} arbitrator with model {arb['model']}")
            continue

        success = run_single_arbitrator(config, arb_key, disagreements_df)

        if not success:
            print(f"\nERROR: Arbitrator {arb_key} failed. Stopping pipeline.")
            return False

        print(f"\n[OK] Arbitrator {arb_key} complete.")

    return True


def run_analysis_stage(config: Dict, dry_run: bool = False) -> bool:
    """Run post-processing analysis."""
    if dry_run:
        print("[DRY RUN] Would run inter-rater agreement analysis")
        print("[DRY RUN] Would run arbitrator comparison analysis")
        return True

    try:
        sys.path.insert(0, str(Path(__file__).parent / 'scripts'))
        from analyze_agreement import run_agreement_analysis
        print("\nRunning inter-rater agreement analysis...")
        run_agreement_analysis(config)
        print("[OK] Agreement analysis complete.")
    except ImportError:
        print("WARNING: analyze_agreement.py not found. Skipping.")
    except Exception as e:
        print(f"WARNING: Agreement analysis failed: {e}")

    try:
        from compare_arbitrators import run_arbitrator_comparison  # noqa: already on sys.path from above
        print("\nRunning arbitrator comparison analysis...")
        run_arbitrator_comparison(config)
        print("[OK] Arbitrator comparison complete.")
    except ImportError:
        print("WARNING: compare_arbitrators.py not found. Skipping.")
    except Exception as e:
        print(f"WARNING: Arbitrator comparison failed: {e}")

    return True


def run_findings_stage(dry_run: bool = False) -> bool:
    """Run Stage 4: Question-level consolidability findings."""
    script = Path(__file__).parent / "04_findings_pipeline.py"

    if dry_run:
        print("[DRY RUN] Would run 04_findings_pipeline.py")
        return True

    if not script.exists():
        print(f"ERROR: {script} not found.")
        return False

    print("\nRunning question-level consolidability analysis...")
    result = subprocess.run([sys.executable, str(script)], cwd=str(Path(__file__).parent))
    if result.returncode != 0:
        print(f"ERROR: 04_findings_pipeline.py exited with code {result.returncode}")
        return False

    print("[OK] Findings analysis complete.")

    # Guard: validate output counts against canonical question_counts.json.
    # If counts diverge, print a clear warning so the inflation bug is immediately visible.
    _validate_findings_counts()

    return True


def _validate_findings_counts():
    """Compare findings pipeline output counts against canonical question_counts.json."""
    import json

    repo = Path(__file__).resolve().parents[2]
    qcj_path = repo / "docs" / "validation" / "question_counts.json"
    ql_path = repo / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_question_level.csv"

    if not qcj_path.exists() or not ql_path.exists():
        print("  [GUARD] Cannot validate findings counts: reference files missing.")
        return

    try:
        import pandas as pd
        with open(qcj_path) as f:
            qcj = json.load(f)

        ql = pd.read_csv(ql_path)
        got_cps = int((ql["survey"] == "CPS").sum())
        got_food = int((ql["survey"] == "FOODAPS").sum())

        exp_cps = qcj["question_level_results"]["CPS"]["unique_questions"]
        exp_food = qcj["question_level_results"]["FoodAPS"]["unique_questions"]

        ok = True
        if got_cps != exp_cps:
            print(f"  [WARNING] Findings guard: CPS row count {got_cps} != canonical {exp_cps}. "
                  "Check 04_findings_pipeline.py for groupby inflation (dedup by question_text, not survey_q_id).")
            ok = False
        if got_food != exp_food:
            print(f"  [WARNING] Findings guard: FoodAPS row count {got_food} != canonical {exp_food}. "
                  "Check 04_findings_pipeline.py for groupby inflation (dedup by question_text, not survey_q_id).")
            ok = False

        if ok:
            print(f"  [GUARD OK] Counts match canonical: CPS={got_cps}, FoodAPS={got_food}")
    except Exception as e:
        print(f"  [GUARD] Could not validate findings counts: {e}")


def run_deliverables_stage(dry_run: bool = False) -> bool:
    """Run Stage 5: Scoring, triage, and expert review deliverables."""
    script = Path(__file__).parent / "05_deliverables_pipeline.py"

    if dry_run:
        print("[DRY RUN] Would run 05_deliverables_pipeline.py")
        return True

    if not script.exists():
        print(f"ERROR: {script} not found.")
        return False

    print("\nRunning deliverables pipeline (scoring, triage, expert tables)...")
    result = subprocess.run([sys.executable, str(script)], cwd=str(Path(__file__).parent))
    if result.returncode != 0:
        print(f"ERROR: 05_deliverables_pipeline.py exited with code {result.returncode}")
        return False

    print("[OK] Deliverables pipeline complete.")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Barrier Coding Pipeline Orchestrator v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py --stage rate --raters openai,anthropic
  python run_pipeline.py --stage arbitrate --arbitrators anthropic
  python run_pipeline.py --stage all
  python run_pipeline.py --validate-config
  python run_pipeline.py --dry-run --stage all
        """
    )

    parser.add_argument(
        '--stage', '-s',
        choices=['rate', 'arbitrate', 'analyze', 'findings', 'deliverables', 'all'],
        default='all',
        help='Pipeline stage to run (default: all)'
    )

    parser.add_argument(
        '--raters', '-r',
        default='all',
        help='Comma-separated raters to run, or "all" (default: all)'
    )

    parser.add_argument(
        '--arbitrators', '-a',
        default='all',
        help='Comma-separated arbitrators to run, or "all" (default: all)'
    )

    parser.add_argument(
        '--validate-config', '-v',
        action='store_true',
        help='Validate config and check API keys, then exit'
    )

    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show execution plan without running'
    )

    parser.add_argument(
        '--config', '-c',
        type=Path,
        default=Path('./config.yaml'),
        help='Path to config file (default: ./config.yaml)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Parse raters/arbitrators
    if args.raters == 'all':
        raters = list(config['raters'].keys())
    else:
        raters = [r.strip() for r in args.raters.split(',')]

    if args.arbitrators == 'all':
        arbitrators = list(config['arbitrators'].keys())
    else:
        arbitrators = [a.strip() for a in args.arbitrators.split(',')]

    # Validate config mode
    if args.validate_config:
        print_banner(config, 'all', list(config['raters'].keys()), list(config['arbitrators'].keys()))
        validate_config(config)
        sys.exit(0)

    # Print banner
    print_banner(config, args.stage, raters, arbitrators)

    if args.dry_run:
        print("[DRY RUN MODE - No actual API calls will be made]")
        print()

    # Ensure directories exist
    ensure_directories(config)

    # Run stages
    success = True

    if args.stage in ('rate', 'all'):
        print("\n" + "=" * 60)
        print("STAGE: RATING")
        print("=" * 60)
        success = run_rating_stage(config, raters, args.dry_run)
        if not success and not args.dry_run:
            sys.exit(1)

    if args.stage in ('arbitrate', 'all') and success:
        print("\n" + "=" * 60)
        print("STAGE: ARBITRATION")
        print("=" * 60)
        success = run_arbitration_stage(config, arbitrators, args.dry_run)
        if not success and not args.dry_run:
            sys.exit(1)

    if args.stage in ('analyze', 'all') and success:
        print("\n" + "=" * 60)
        print("STAGE: ANALYSIS")
        print("=" * 60)
        run_analysis_stage(config, args.dry_run)

    if args.stage in ('findings', 'all') and success:
        print("\n" + "=" * 60)
        print("STAGE: FINDINGS")
        print("=" * 60)
        success = run_findings_stage(args.dry_run)
        if not success and not args.dry_run:
            sys.exit(1)

    if args.stage in ('deliverables', 'all') and success:
        print("\n" + "=" * 60)
        print("STAGE: DELIVERABLES")
        print("=" * 60)
        success = run_deliverables_stage(args.dry_run)
        if not success and not args.dry_run:
            sys.exit(1)

    # Final summary
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    if args.dry_run:
        print("\n[DRY RUN] No actual work was performed.")
    else:
        print(f"\nOutputs written to: {config['paths']['output_dir']}/")


if __name__ == "__main__":
    main()
