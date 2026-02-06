#!/usr/bin/env python3
"""
Generate visualization of harmonization code distribution.

Shows F1/F2/F3 counts and breakdown of F3 by barrier sub-codes.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Paths
# Path setup for post-restructure layout
SRC_DIR = Path(__file__).resolve().parent.parent    # .../src/
REPO_ROOT = SRC_DIR.parent                           # repo root
sys.path.insert(0, str(SRC_DIR))                     # enables lib imports
DATA_FILE = BASE_DIR / "output/analysis/final_verdicts.csv"
OUTPUT_FILE = BASE_DIR / "presentation/images/harmonization_distribution.png"

def load_data():
    """Load final verdicts data."""
    df = pd.read_csv(DATA_FILE)
    print(f"Loaded {len(df)} pairs")
    return df

def create_visualization(df):
    """Create combined visualization."""
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['font.size'] = 11
    plt.rcParams['axes.labelsize'] = 12
    plt.rcParams['axes.titlesize'] = 14

    # Create figure with 2 subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # --- Left plot: F1/F2/F3 distribution ---
    feasibility_counts = df['final_feasibility'].value_counts().sort_index()

    colors_feas = {'F1': '#4CAF50', 'F2': '#FFC107', 'F3': '#F44336'}
    colors = [colors_feas.get(f, '#999999') for f in feasibility_counts.index]

    bars1 = ax1.bar(feasibility_counts.index, feasibility_counts.values,
                    color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)

    ax1.set_xlabel('Feasibility Code', fontweight='bold')
    ax1.set_ylabel('Number of Question Pairs', fontweight='bold')
    ax1.set_title('Overall Harmonization Feasibility', fontweight='bold', pad=20)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}\n({height/len(df)*100:.1f}%)',
                ha='center', va='bottom', fontweight='bold', fontsize=11)

    # Add legend for F1/F2/F3
    from matplotlib.patches import Patch
    legend_elements1 = [
        Patch(facecolor='#4CAF50', label='F1: Direct recode'),
        Patch(facecolor='#FFC107', label='F2: Statistical adjustment'),
        Patch(facecolor='#F44336', label='F3: Incompatible')
    ]
    ax1.legend(handles=legend_elements1, loc='upper right', framealpha=0.9)

    ax1.grid(axis='y', alpha=0.3)
    ax1.set_axisbelow(True)

    # --- Right plot: F3 barrier breakdown ---
    f3_data = df[df['final_feasibility'] == 'F3'].copy()

    # Extract barrier codes (handle NaN and extract primary code)
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
    ax2.set_xlabel('Number of Question Pairs', fontweight='bold')
    ax2.set_ylabel('Barrier Sub-Code', fontweight='bold')
    ax2.set_title('F3 Pairs by Barrier Sub-Code (Top 10)', fontweight='bold', pad=20)

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
    fig.suptitle('Harmonization Code Distribution (1,598 Question Pairs)',
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

    print("\nFeasibility Distribution:")
    feas_counts = df['final_feasibility'].value_counts().sort_index()
    for code, count in feas_counts.items():
        pct = count / len(df) * 100
        print(f"  {code}: {count:4d} ({pct:5.1f}%)")

    print(f"\nTotal: {len(df)} pairs")

    # F3 breakdown
    f3_data = df[df['final_feasibility'] == 'F3']
    print(f"\nF3 Pairs: {len(f3_data)}")
    print("\nTop 10 Barrier Codes (F3 only):")
    barrier_counts = f3_data['final_barrier_code'].value_counts().head(10)
    for code, count in barrier_counts.items():
        pct = count / len(f3_data) * 100
        print(f"  {code:8s}: {count:4d} ({pct:5.1f}%)")

def main():
    """Main execution."""
    print("=" * 60)
    print("HARMONIZATION CODE DISTRIBUTION VISUALIZATION")
    print("=" * 60)

    df = load_data()
    print_summary(df)
    create_visualization(df)

    print("\n" + "=" * 60)
    print("COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
