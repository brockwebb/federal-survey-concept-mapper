#!/usr/bin/env python3
"""
Master pipeline runner for federal survey concept mapping.

Runs complete analysis from initial categorization through arbitration.

Steps:
1. Clean previous runs (optional)
2. Initial categorization (gpt-5-mini + claude-haiku-4-5)
3. Comparison analysis
4. Failure/disagreement analysis
5. Agentic arbitration with feedback loop
6. Final reconciliation and outputs

Usage:
    python run_pipeline.py --clean     # Full clean re-run
    python run_pipeline.py --from 3    # Resume from step 3
    python run_pipeline.py --only 5    # Run only step 5
"""

import argparse
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import shutil

# Pipeline configuration
STEPS = {
    1: {
        'name': 'Initial Categorization - Claude',
        'script': 'categorize_claude.py',
        'description': 'Categorize all questions with claude-haiku-4-5',
        'outputs': [
            '../output/results/results_claude.jsonl'
        ]
    },
    2: {
        'name': 'Initial Categorization - OpenAI',
        'script': 'categorize_openai.py',
        'description': 'Categorize all questions with gpt-5-mini',
        'outputs': [
            '../output/results/results_openai.jsonl'
        ]
    },
    3: {
        'name': 'Comparison Analysis',
        'script': 'compare_llm_results.py',
        'description': 'Compare models and calculate agreement metrics',
        'outputs': [
            '../output/comparison/agreement_summary.csv',
            '../output/comparison/full_comparison.csv',
            '../output/comparison/comparison_overview.png'
        ]
    },
    4: {
        'name': 'Failure/Disagreement Analysis',
        'script': 'analyze_failures_disagreements.py',
        'description': 'Identify patterns in failures and disagreements',
        'outputs': [
            '../output/analysis/failures.csv',
            '../output/analysis/arbitration_candidates.csv'
        ]
    },
    5: {
        'name': 'Final Arbitration (Dual-Modal)',
        'script': 'arbitrate_final.py',
        'description': 'Arbitrate disagreements with dual-modal support and confidence tiers',
        'outputs': [
            '../output/arbitration_final/arbitration_results.csv',
            '../output/arbitration_final/all_disagreement_resolutions.csv'
        ]
    },
    6: {
        'name': 'Final Reconciliation & Summary',
        'script': 'create_final_outputs.py',
        'description': 'Create master dataset and summary visualizations',
        'outputs': [
            '../output/final/master_dataset.csv',
            '../output/final/survey_concept_matrix.csv',
            '../output/final/summary_dashboard.png',
            '../output/final/README.md'
        ]
    }
}

def print_header(text):
    """Print formatted header."""
    print("\n" + "="*70)
    print(text.center(70))
    print("="*70 + "\n")

def clean_outputs():
    """Remove all output directories for clean re-run."""
    print("Cleaning previous outputs...")
    
    dirs_to_clean = [
        '../output/results',
        '../output/comparison',
        '../output/analysis',
        '../output/arbitration',
        '../output/arbitration_agentic',
        '../output/arbitration_final',
        '../output/final'
    ]
    
    for dir_path in dirs_to_clean:
        path = Path(dir_path)
        if path.exists():
            shutil.rmtree(path)
            print(f"  ✓ Removed {dir_path}")
    
    # Also remove checkpoints
    checkpoint_files = [
        '../output/categorization_checkpoint.json',
        '../output/categorization_checkpoint.tmp'
    ]
    for checkpoint_file in checkpoint_files:
        checkpoint = Path(checkpoint_file)
        if checkpoint.exists():
            checkpoint.unlink()
            print(f"  ✓ Removed {checkpoint.name}")
    
    print("\nClean complete!\n")

def check_outputs(step_num):
    """Check if step outputs exist and are complete."""
    step = STEPS[step_num]
    
    # Check all output files exist
    for output in step['outputs']:
        if not Path(output).exists():
            return False
    
    # For Steps 1-2 (categorization), verify line count
    if step_num in [1, 2]:
        expected_questions = 6987  # Total questions in dataset
        output_file = step['outputs'][0]
        
        try:
            with open(output_file, 'r') as f:
                line_count = sum(1 for _ in f)
            
            if line_count < expected_questions:
                print(f"  ⚠️  {output_file} has {line_count} lines, expected {expected_questions}")
                return False
        except Exception:
            return False
    
    return True

def run_step(step_num):
    """Run a pipeline step."""
    step = STEPS[step_num]
    
    print(f"\n{'─'*70}")
    print(f"Step {step_num}: {step['name']}")
    print(f"{'─'*70}")
    print(f"Description: {step['description']}")
    print(f"Script: {step['script']}\n")
    
    # Check if already complete
    if check_outputs(step_num):
        print("⚠️  Outputs already exist. Skipping...")
        print("   Use --clean to re-run from scratch\n")
        return True
    
    # Run the script
    start_time = datetime.now()
    print(f"Started at: {start_time.strftime('%H:%M:%S')}\n")
    
    try:
        result = subprocess.run(
            ['python', step['script']],
            cwd=Path(__file__).parent,
            capture_output=False,
            text=True,
            check=True
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n✓ Step {step_num} complete!")
        print(f"  Duration: {duration}")
        print(f"  Finished at: {end_time.strftime('%H:%M:%S')}")
        
        # Verify outputs
        missing = [o for o in step['outputs'] if not Path(o).exists()]
        if missing:
            print(f"\n⚠️  Warning: Some expected outputs missing:")
            for m in missing:
                print(f"    - {m}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Step {step_num} failed!")
        print(f"  Error code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Pipeline interrupted by user")
        return False

def print_summary(completed_steps, failed_steps):
    """Print pipeline summary."""
    print_header("PIPELINE SUMMARY")
    
    print("Completed steps:")
    for step_num in completed_steps:
        step = STEPS[step_num]
        print(f"  ✓ Step {step_num}: {step['name']}")
    
    if failed_steps:
        print("\nFailed steps:")
        for step_num in failed_steps:
            step = STEPS[step_num]
            print(f"  ✗ Step {step_num}: {step['name']}")
    
    print("\nOutputs location: ../output/")
    print("\nKey deliverables:")
    print("  - final/master_dataset.csv - Complete categorizations")
    print("  - final/survey_concept_matrix.csv - Survey × concept aggregation")
    print("  - final/summary_dashboard.png - Visual overview")
    print("  - final/README.md - Summary report")
    print("\nIntermediate outputs:")
    print("  - results/results_openai.jsonl, results_claude.jsonl")
    print("  - comparison/agreement_summary.csv")
    print("  - analysis/arbitration_candidates.csv")
    print("  - arbitration_agentic/agentic_arbitration_results.csv")

def main():
    parser = argparse.ArgumentParser(
        description='Run federal survey concept mapping pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_pipeline.py              # Run all steps (skip completed)
  python run_pipeline.py --clean      # Clean re-run from scratch
  python run_pipeline.py --from 3     # Run from step 3 onwards
  python run_pipeline.py --only 4     # Run only step 4
        """
    )
    
    parser.add_argument('--clean', action='store_true',
                       help='Clean all outputs before running')
    parser.add_argument('--from', dest='from_step', type=int, metavar='N',
                       help='Start from step N')
    parser.add_argument('--only', type=int, metavar='N',
                       help='Run only step N')
    
    args = parser.parse_args()
    
    print_header("FEDERAL SURVEY CONCEPT MAPPING PIPELINE")
    
    print("Pipeline steps:")
    for step_num, step in STEPS.items():
        status = "✓" if check_outputs(step_num) else " "
        print(f"  [{status}] Step {step_num}: {step['name']}")
    
    # Clean if requested
    if args.clean:
        print()
        response = input("This will delete all output files. Continue? [y/N]: ")
        if response.lower() == 'y':
            clean_outputs()
        else:
            print("Aborted.")
            return
    
    # Determine which steps to run
    if args.only:
        steps_to_run = [args.only]
    elif args.from_step:
        steps_to_run = list(range(args.from_step, len(STEPS) + 1))
    else:
        steps_to_run = list(range(1, len(STEPS) + 1))
    
    print(f"\nRunning steps: {steps_to_run}\n")
    input("Press Enter to start...")
    
    # Run pipeline
    start_time = datetime.now()
    completed_steps = []
    failed_steps = []
    
    for step_num in steps_to_run:
        if step_num not in STEPS:
            print(f"⚠️  Step {step_num} does not exist. Skipping...")
            continue
        
        success = run_step(step_num)
        
        if success:
            completed_steps.append(step_num)
        else:
            failed_steps.append(step_num)
            print(f"\nPipeline stopped at step {step_num}")
            break
    
    end_time = datetime.now()
    total_duration = end_time - start_time
    
    # Summary
    print_summary(completed_steps, failed_steps)
    
    print(f"\nTotal pipeline duration: {total_duration}")
    print(f"Finished at: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not failed_steps:
        print("\n✓ Pipeline complete!")
    else:
        print("\n⚠️  Pipeline incomplete - see failed steps above")
        sys.exit(1)

if __name__ == '__main__':
    main()
