#!/usr/bin/env python3
"""
Assemble the complete report from individual sections.

This script:
1. Regenerates required figures from source data
2. Copies figures to final_report/figures/
3. Copies data files to final_report/data/
4. Assembles all sections into FULL_REPORT.md

Run from src/ directory:
    python assemble_report.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

# Base paths (script runs from src/)
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'
FINAL_REPORT_DIR = BASE_DIR / 'final_report'
SECTIONS_DIR = FINAL_REPORT_DIR / 'sections'
FIGURES_DIR = FINAL_REPORT_DIR / 'figures'
DATA_DIR = FINAL_REPORT_DIR / 'data'
OUTPUT_FILE = FINAL_REPORT_DIR / 'FULL_REPORT.md'

# Scripts that generate figures (run in order)
FIGURE_SCRIPTS = [
    'create_figure_02_agreement.py',      # Figure 2: Model agreement
    'generate_coverage_analysis.py',       # Figure 4: Horizontal bars + others
]

# Figures to include in report (source -> destination name)
FIGURES = {
    OUTPUT_DIR / 'visualizations' / 'figure_02_model_agreement.png': 'figure_02_model_agreement.png',
    OUTPUT_DIR / 'visualizations' / 'horizontal_bars_all_subtopics.png': 'figure_04_topic_distribution.png',
}

# Data files to include (source -> destination name)
DATA_FILES = {
    OUTPUT_DIR / 'final' / 'master_dataset.csv': 'master_dataset.csv',
    OUTPUT_DIR / 'final' / 'survey_concept_matrix.csv': 'survey_concept_matrix.csv',
}

# Section order for report assembly
SECTIONS = [
    '00_executive_summary.md',
    '01_abstract.md',
    '02_introduction.md',
    '03_background.md',
    '04_methodology.md',
    '05_data_collection.md',
    '06_categorization_approach.md',
    '07_results.md',
    '08_coverage_analysis.md',
    '09_consolidation_opportunities.md',
    '10_discussion.md',
    '11_limitations.md',
    '12_recommendations.md',
    '13_conclusion.md',
    '14_appendices.md',
    'references.md'
]


def run_figure_scripts():
    """Run scripts to regenerate figures from source data."""
    print("\n[1/4] Regenerating figures from source data...")
    print("-" * 50)
    
    success_count = 0
    for script in FIGURE_SCRIPTS:
        script_path = SRC_DIR / script
        if not script_path.exists():
            print(f"  ⚠️  MISSING SCRIPT: {script}")
            continue
        
        print(f"  Running {script}...")
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(SRC_DIR),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            if result.returncode == 0:
                print(f"    ✓ {script} completed")
                success_count += 1
            else:
                print(f"    ✗ {script} failed:")
                print(f"      {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"    ✗ {script} timed out")
        except Exception as e:
            print(f"    ✗ {script} error: {e}")
    
    print(f"\n  Ran {success_count}/{len(FIGURE_SCRIPTS)} scripts successfully")
    return success_count == len(FIGURE_SCRIPTS)


def copy_figures():
    """Copy figures from output/ to final_report/figures/."""
    print("\n[2/4] Copying figures to final_report/figures/...")
    print("-" * 50)
    
    # Ensure figures directory exists
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for source, dest_name in FIGURES.items():
        dest = FIGURES_DIR / dest_name
        if not source.exists():
            print(f"  ⚠️  MISSING: {source.name}")
            continue
        shutil.copy2(source, dest)
        print(f"  ✓ {source.name} → {dest_name}")
        copied += 1
    
    print(f"\n  Copied {copied}/{len(FIGURES)} figures")
    return copied == len(FIGURES)


def copy_data_files():
    """Copy data files from output/ to final_report/data/."""
    print("\n[3/4] Copying data files to final_report/data/...")
    print("-" * 50)
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for source, dest_name in DATA_FILES.items():
        dest = DATA_DIR / dest_name
        if not source.exists():
            print(f"  ⚠️  MISSING: {source.name}")
            continue
        shutil.copy2(source, dest)
        print(f"  ✓ {source.name} → {dest_name}")
        copied += 1
    
    print(f"\n  Copied {copied}/{len(DATA_FILES)} data files")
    return copied == len(DATA_FILES)


def assemble_report():
    """Assemble all sections into complete report."""
    print("\n[4/4] Assembling report sections...")
    print("-" * 50)
    
    # Start with title page
    content = []
    content.append("# From Weeks to Hours: Automated Concept Mapping for Federal Survey Analysis")
    content.append("## A Proof-of-Concept for AI-Assisted Survey Ecosystem Analysis")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## ⚠️ DRAFT — NOT FOR DISTRIBUTION")
    content.append("")
    content.append("*This document is a working draft and has not been finalized. Content is subject to revision.*")
    content.append("")
    content.append("---")
    content.append("")
    content.append("**Report Date**: January 2025 (Draft)")
    content.append("")
    content.append("---")
    content.append("")
    content.append("**Disclaimer**: This is exploratory research. Views expressed are the author's own.")
    content.append("")
    content.append("---")
    content.append("")
    content.append("## Document Information")
    content.append("")
    content.append("- **Total Questions Analyzed**: 6,987")
    content.append("- **Federal Surveys Covered**: 46")
    content.append("- **Taxonomy**: U.S. Census Bureau Survey Explorer Topics")
    content.append("- **Methodology**: Dual-LLM categorization with arbitration")
    content.append("- **Success Rate**: 99.5%")
    content.append("- **Processing Time**: ~2 hours")
    content.append("- **Production Cost**: ~$15")
    content.append("")
    content.append("---")
    content.append("")
    content.append("\\newpage")
    content.append("")
    
    # Append each section
    sections_found = 0
    for i, section_file in enumerate(SECTIONS, 1):
        section_path = SECTIONS_DIR / section_file
        
        if not section_path.exists():
            print(f"  ⚠️  MISSING: {section_file}")
            continue
        
        print(f"  [{i:2d}/{len(SECTIONS)}] {section_file}")
        sections_found += 1
        
        with open(section_path, 'r', encoding='utf-8') as f:
            section_content = f.read()
        
        content.append(section_content)
        content.append("")
        
        # Don't add page break after references (it's the last section)
        if section_file != 'references.md':
            content.append("\\newpage")
            content.append("")
    
    # Write assembled report
    full_content = '\n'.join(content)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"\n  Assembled {sections_found}/{len(SECTIONS)} sections")
    return sections_found == len(SECTIONS), len(full_content)


def main():
    """Run complete report build."""
    print("=" * 70)
    print("FEDERAL SURVEY CONCEPT MAPPING - REPORT BUILD")
    print("=" * 70)
    
    scripts_ok = run_figure_scripts()
    figures_ok = copy_figures()
    data_ok = copy_data_files()
    sections_ok, char_count = assemble_report()
    
    print("\n" + "=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)
    print(f"\nOutput: {OUTPUT_FILE}")
    print(f"Total length: {char_count:,} characters")
    print(f"Estimated pages: ~{char_count // 3000} pages")
    
    all_ok = scripts_ok and figures_ok and data_ok and sections_ok
    
    if all_ok:
        print("\n✓ All steps completed successfully")
        print("✓ DRAFT report is ready for review")
    else:
        print("\n⚠️  Some steps had issues - check warnings above")
    
    return 0 if all_ok else 1


if __name__ == '__main__':
    exit(main())
