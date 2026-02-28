#!/usr/bin/env python3
"""
Generate question-level consolidation distribution visualization.

Shows F1/F2/F3 counts by source survey (CPS vs FoodAPS) and F3 barrier breakdown.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
ANALYSIS_DIR = REPO_ROOT / "docs" / "stages" / "03_harmonization" / "data" / "analysis"
QUESTION_DATA = ANALYSIS_DIR / "stage4_question_best_matches.csv"
PAIR_DATA = ANALYSIS_DIR / "final_verdicts.csv"
OUTPUT_FILE = REPO_ROOT / "output" / "report_03" / "visuals" / "question_consolidation_distribution.png"

def load_data():
    """Load question-level and pair-level data."""
    questions_df = pd.read_csv(QUESTION_DATA)
    pairs_df = pd.read_csv(PAIR_DATA)

    print(f"Loaded {len(questions_df)} questions")

    # Check actual survey values
    survey_counts = questions_df['survey'].value_counts()
    for survey, count in survey_counts.items():
        print(f"  {survey}: {count}")

    # Join to get barrier codes for F3 questions
    questions_df = questions_df.merge(
        pairs_df[['pair_id', 'final_barrier_code']],
        on='pair_id',
        how='left'
    )

    return questions_df

def create_visualization(df):
    """Create combined visualization."""
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Left plot: F1/F2/F3 by survey ---
    # Create crosstab
    ct = pd.crosstab(df['survey'], df['best_feasibility'])

    # Ensure F1, F2, F3 order
    for col in ['F1', 'F2', 'F3']:
        if col not in ct.columns:
            ct[col] = 0
    ct = ct[['F1', 'F2', 'F3']]

    colors_feas = ['#4CAF50', '#FFC107', '#F44336']  # Green, Yellow, Red

    ct.plot(kind='bar', ax=ax1, color=colors_feas, alpha=0.8,
            edgecolor='black', linewidth=1.5, width=0.7)

    ax1.set_xlabel('Source Survey', fontweight='bold')
    ax1.set_ylabel('Number of Questions', fontweight='bold')
    ax1.set_title('Question Consolidation by Survey', fontweight='bold', pad=20)
    ax1.set_xticklabels(ax1.get_xticklabels(), rotation=0)
    ax1.legend(title='Feasibility', labels=['F1: Direct recode', 'F2: Statistical adjustment', 'F3: Incompatible'])

    # Add value labels on bars
    for container in ax1.containers:
        ax1.bar_label(container, fontweight='bold', fontsize=10)

    ax1.grid(axis='y', alpha=0.3)
    ax1.set_axisbelow(True)

    # --- Right plot: F3 barrier breakdown ---
    f3_data = df[df['best_feasibility'] == 'F3'].copy()

    # Count barrier codes
    barrier_counts = f3_data['final_barrier_code'].dropna().value_counts()

    # Get top 10 barrier codes
    top_barriers = barrier_counts.head(10)

    # Color code by main category
    def get_color(code):
        if pd.isna(code):
            return '#999999'
        code_str = str(code)
        if code_str.startswith('CC'):
            return '#E57373'  # Red for Construct
        elif code_str.startswith('TC'):
            return '#64B5F6'  # Blue for Temporal
        elif code_str.startswith('RS'):
            return '#81C784'  # Green for Response Scale
        elif code_str.startswith('PC'):
            return '#FFD54F'  # Yellow for Population
        elif code_str.startswith('MC'):
            return '#BA68C8'  # Purple for Mode/Context
        elif code_str.startswith('PM'):
            return '#FF8A65'  # Orange for Processing
        else:
            return '#999999'  # Gray for other

    colors2 = [get_color(code) for code in top_barriers.index]

    bars2 = ax2.barh(range(len(top_barriers)), top_barriers.values,
                     color=colors2, alpha=0.8, edgecolor='black', linewidth=1)

    ax2.set_yticks(range(len(top_barriers)))
    ax2.set_yticklabels(top_barriers.index)
    ax2.set_xlabel('Number of Questions', fontweight='bold')
    ax2.set_ylabel('Barrier Sub-Code', fontweight='bold')
    ax2.set_title('F3 Questions by Barrier Sub-Code (Top 10)', fontweight='bold', pad=20)

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars2, top_barriers.values)):
        width = bar.get_width()
        ax2.text(width, bar.get_y() + bar.get_height()/2.,
                f' {int(val)} ({val/len(f3_data)*100:.1f}%)',
                ha='left', va='center', fontweight='bold', fontsize=10)

    # Add legend for barrier categories
    from matplotlib.patches import Patch
    legend_elements2 = [
        Patch(facecolor='#E57373', label='CC: Construct/Concept'),
        Patch(facecolor='#64B5F6', label='TC: Temporal'),
        Patch(facecolor='#81C784', label='RS: Response Scale'),
        Patch(facecolor='#FFD54F', label='PC: Population'),
        Patch(facecolor='#BA68C8', label='MC: Mode/Context'),
        Patch(facecolor='#FF8A65', label='PM: Processing/Metadata')
    ]
    ax2.legend(handles=legend_elements2, loc='lower right', framealpha=0.9, fontsize=9)

    ax2.grid(axis='x', alpha=0.3)
    ax2.set_axisbelow(True)
    ax2.invert_yaxis()  # Top barrier at top

    # Overall title
    fig.suptitle(f'Question-Level Consolidation Distribution ({len(df)} Questions)',
                 fontsize=16, fontweight='bold', y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.96])

    # Save
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUTPUT_FILE, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size / 1024:.1f} KB")

    plt.close()

def print_summary(df):
    """Print summary statistics."""
    print("\n=== Summary Statistics ===")

    print("\nFeasibility Distribution by Survey:")
    ct = pd.crosstab(df['survey'], df['best_feasibility'], margins=True)
    print(ct)

    print("\nConsolidation Rates by Survey:")
    for survey in df['survey'].unique():
        survey_df = df[df['survey'] == survey]
        consolidable = len(survey_df[survey_df['best_feasibility'].isin(['F1', 'F2'])])
        total = len(survey_df)
        rate = consolidable / total * 100 if total > 0 else 0
        print(f"  {survey:8s}: {consolidable:3d}/{total:3d} ({rate:5.1f}%)")

    # F3 breakdown
    f3_data = df[df['best_feasibility'] == 'F3']
    print(f"\nF3 Questions: {len(f3_data)}")
    print("\nTop 10 Barrier Codes (F3 only):")
    barrier_counts = f3_data['final_barrier_code'].value_counts().head(10)
    for code, count in barrier_counts.items():
        pct = count / len(f3_data) * 100
        print(f"  {code:8s}: {count:3d} ({pct:5.1f}%)")

def main():
    """Main execution."""
    print("=" * 60)
    print("QUESTION-LEVEL CONSOLIDATION DISTRIBUTION")
    print("=" * 60)

    df = load_data()
    print_summary(df)
    create_visualization(df)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
