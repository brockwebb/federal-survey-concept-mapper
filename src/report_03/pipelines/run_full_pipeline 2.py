#!/usr/bin/env python3
"""
Master Pipeline Runner: Dual-Model Barrier Coding with Arbitration
Report 03: Harmonization Constraints

Executes the complete pipeline:
1. Dual-model coding (gpt-4o-mini + claude-haiku-4-5)
2. Agreement analysis & confusion matrices
3. Third-model arbitration (claude-opus-4-5)
4. Final compilation

Usage:
    python run_full_pipeline.py [--skip-coding] [--skip-arbitration] [--force]

Options:
    --skip-coding      Skip Phase 1 if results already exist
    --skip-arbitration Skip Phase 3 if arbitration results exist
    --force            Overwrite existing outputs
"""

import subprocess
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Paths
REPORT_DIR = Path(__file__).parent
OUTPUT_DIR = REPORT_DIR / "output"
RESULTS_DIR = OUTPUT_DIR / "results"
ANALYSIS_DIR = OUTPUT_DIR / "analysis"
CONFUSION_DIR = ANALYSIS_DIR / "confusion_analysis"

def log(msg: str):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")

def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    log(f"Starting: {description}")
    log(f"Script: {script_name}")
    
    result = subprocess.run(
        [sys.executable, script_name],
        cwd=REPORT_DIR,
        capture_output=False
    )
    
    if result.returncode == 0:
        log(f"✓ Completed: {description}")
        return True
    else:
        log(f"✗ Failed: {description} (exit code {result.returncode})")
        return False

def check_file_exists(path: Path, description: str) -> bool:
    """Check if file exists and log status."""
    exists = path.exists()
    status = "✓ exists" if exists else "✗ missing"
    log(f"  {description}: {status}")
    return exists

def main():
    parser = argparse.ArgumentParser(description="Run full barrier coding pipeline")
    parser.add_argument("--skip-coding", action="store_true", 
                        help="Skip Phase 1 if results exist")
    parser.add_argument("--skip-arbitration", action="store_true",
                        help="Skip Phase 3 if results exist")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing outputs")
    args = parser.parse_args()
    
    print("="*70)
    print("DUAL-MODEL BARRIER CODING PIPELINE WITH ARBITRATION")
    print("Report 03: Harmonization Constraints")
    print("="*70)
    
    # Check prerequisites
    log("Checking prerequisites...")
    prereqs_ok = True
    prereqs_ok &= check_file_exists(REPORT_DIR / "data" / "cps_comparison_merged.csv", "CPS data")
    prereqs_ok &= check_file_exists(REPORT_DIR / "data" / "foodaps_comparison_merged.csv", "FoodAPS data")
    prereqs_ok &= check_file_exists(REPORT_DIR / "barrier_coding_pipeline.py", "Coding script")
    prereqs_ok &= check_file_exists(REPORT_DIR / "analyze_barrier_results.py", "Analysis script")
    prereqs_ok &= check_file_exists(REPORT_DIR / "confusion_matrix_analysis.py", "Confusion matrix script")
    prereqs_ok &= check_file_exists(REPORT_DIR / "arbitration_pipeline.py", "Arbitration script")
    
    if not prereqs_ok:
        log("ERROR: Missing prerequisites. Aborting.")
        sys.exit(1)
    
    # =========================================================================
    # PHASE 1: Dual-Model Coding
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 1: DUAL-MODEL CODING")
    print("="*70)
    
    coding_exists = (
        (RESULTS_DIR / "barrier_results_openai.jsonl").exists() and
        (RESULTS_DIR / "barrier_results_claude.jsonl").exists()
    )
    
    if coding_exists and args.skip_coding and not args.force:
        log("Skipping Phase 1: Results already exist (use --force to overwrite)")
    else:
        if not run_script("barrier_coding_pipeline.py", "Dual-model barrier coding"):
            log("ERROR: Phase 1 failed. Aborting.")
            sys.exit(1)
    
    # =========================================================================
    # PHASE 2: Agreement Analysis
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 2: AGREEMENT ANALYSIS")
    print("="*70)
    
    # Always run analysis to get fresh stats
    if not run_script("analyze_barrier_results.py", "Merge and analyze results"):
        log("ERROR: Analysis failed. Aborting.")
        sys.exit(1)
    
    if not run_script("confusion_matrix_analysis.py", "Generate confusion matrices"):
        log("ERROR: Confusion matrix analysis failed. Aborting.")
        sys.exit(1)
    
    # =========================================================================
    # PHASE 3: Arbitration
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 3: ARBITRATION")
    print("="*70)
    
    arbitration_exists = (CONFUSION_DIR / "arbitration_results.jsonl").exists()
    
    if arbitration_exists and args.skip_arbitration and not args.force:
        log("Skipping Phase 3: Arbitration results exist (use --force to overwrite)")
    else:
        if not run_script("arbitration_pipeline.py", "Third-model arbitration"):
            log("WARNING: Arbitration had issues. Check output manually.")
            # Don't abort - partial results may still be useful
    
    # =========================================================================
    # PHASE 4: Final Compilation (built into arbitration_pipeline.py)
    # =========================================================================
    print("\n" + "="*70)
    print("PHASE 4: FINAL COMPILATION")
    print("="*70)
    
    final_file = CONFUSION_DIR / "barrier_coding_final.csv"
    if final_file.exists():
        log(f"✓ Final results: {final_file}")
        
        # Quick stats
        import pandas as pd
        df = pd.read_csv(final_file)
        log(f"  Total pairs: {len(df)}")
        
        if 'final_barrier_L1' in df.columns:
            log(f"  Barrier distribution:")
            for code, count in df['final_barrier_L1'].value_counts().head(5).items():
                log(f"    {code}: {count} ({100*count/len(df):.1f}%)")
        
        if 'final_feasibility' in df.columns:
            log(f"  Feasibility distribution:")
            for code, count in df['final_feasibility'].value_counts().items():
                log(f"    {code}: {count} ({100*count/len(df):.1f}%)")
    else:
        log("WARNING: Final results file not found. Check arbitration output.")
    
    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "="*70)
    print("PIPELINE COMPLETE")
    print("="*70)
    
    log("Output files:")
    outputs = [
        (RESULTS_DIR / "barrier_results_openai.jsonl", "OpenAI codings"),
        (RESULTS_DIR / "barrier_results_claude.jsonl", "Claude codings"),
        (ANALYSIS_DIR / "barrier_coding_merged.csv", "Merged results"),
        (ANALYSIS_DIR / "barrier_coding_summary.json", "Agreement stats"),
        (CONFUSION_DIR / "barrier_L1_confusion_matrix.png", "L1 confusion matrix"),
        (CONFUSION_DIR / "barrier_full_confusion_matrix.png", "Full code confusion matrix"),
        (CONFUSION_DIR / "feasibility_confusion_matrix.png", "Feasibility confusion matrix"),
        (CONFUSION_DIR / "arbitration_results.jsonl", "Arbitration results"),
        (CONFUSION_DIR / "barrier_coding_final.csv", "Final coded dataset"),
    ]
    
    for path, desc in outputs:
        status = "✓" if path.exists() else "✗"
        log(f"  {status} {desc}: {path.name}")
    
    print("\n" + "="*70)
    log("See methodology_log.md for decision rationale")
    log("See barrier_coding_pipeline_documentation.md for full methodology")
    print("="*70)

if __name__ == "__main__":
    main()
