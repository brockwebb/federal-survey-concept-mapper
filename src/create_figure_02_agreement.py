#!/usr/bin/env python3
"""
Generate Figure 2: Model Agreement Visualization
Bar chart showing agreement metrics and Cohen's Kappa.
"""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set style
sns.set_style('whitegrid')
plt.rcParams['figure.facecolor'] = 'white'

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Left plot: Agreement Rates
categories = ['Topic\nAgreement', 'Subtopic\nAgreement']
values = [89.4, 68.7]
colors = ['#4CAF50', '#2196F3']

bars1 = ax1.bar(categories, values, color=colors, alpha=0.8, edgecolor='black', linewidth=2)

# Add value labels on bars
for bar, val in zip(bars1, values):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{val}%',
             ha='center', va='bottom', fontsize=14, fontweight='bold')

# Add reference line at 100%
ax1.axhline(y=100, color='gray', linestyle='--', linewidth=1, alpha=0.5)

ax1.set_ylabel('Agreement Rate (%)', fontsize=13, fontweight='bold')
ax1.set_title('Model Agreement Rates\n(GPT-5-mini vs Claude Haiku 4.5)', 
              fontsize=14, fontweight='bold', pad=20)
ax1.set_ylim(0, 105)
ax1.grid(axis='y', alpha=0.3)

# Add annotation
ax1.text(0.5, 50, '6,218/6,954\nquestions agreed',
         ha='center', va='center', fontsize=10, style='italic',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

# Right plot: Cohen's Kappa
categories2 = ['Topics\n(κ = 0.842)', 'Subtopics\n(κ = 0.692)']
kappa_values = [0.842, 0.692]
colors2 = ['#4CAF50', '#2196F3']

bars2 = ax2.bar(categories2, kappa_values, color=colors2, alpha=0.8, edgecolor='black', linewidth=2)

# Add value labels on bars
for bar, val in zip(bars2, kappa_values):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 0.02,
             f'{val:.3f}',
             ha='center', va='bottom', fontsize=14, fontweight='bold')

# Add interpretation zones
ax2.axhspan(0.81, 1.0, alpha=0.1, color='green', label='Almost Perfect (>0.80)')
ax2.axhspan(0.61, 0.80, alpha=0.1, color='yellow', label='Substantial (0.61-0.80)')
ax2.axhspan(0.41, 0.60, alpha=0.1, color='orange', label='Moderate (0.41-0.60)')

# Add horizontal lines for thresholds
ax2.axhline(y=0.80, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
ax2.axhline(y=0.60, color='orange', linestyle='--', linewidth=1.5, alpha=0.7)

ax2.set_ylabel('Cohen\'s Kappa (κ)', fontsize=13, fontweight='bold')
ax2.set_title('Inter-Rater Reliability\n(Beyond-Chance Agreement)', 
              fontsize=14, fontweight='bold', pad=20)
ax2.set_ylim(0, 1.0)
ax2.legend(loc='lower right', fontsize=9, framealpha=0.9)
ax2.grid(axis='y', alpha=0.3)

# Add interpretation text
ax2.text(0.5, 0.5, '"Almost Perfect"\nAgreement',
         ha='center', va='center', fontsize=10, style='italic',
         bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))

ax2.text(1.5, 0.35, '"Substantial"\nAgreement',
         ha='center', va='center', fontsize=10, style='italic',
         bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.5))

# Overall title
fig.suptitle('Dual-Model Agreement Analysis: GPT-5-mini vs Claude Haiku 4.5',
             fontsize=16, fontweight='bold', y=1.00)

# Add subtitle
fig.text(0.5, 0.02, 
         'Both models categorized 6,987 questions independently. High agreement indicates consistent semantic understanding across architectures.',
         ha='center', fontsize=11, style='italic', wrap=True)

plt.tight_layout(rect=[0, 0.03, 1, 0.98])
plt.savefig('../final_report/figures/figure_02_model_agreement.png', dpi=300, bbox_inches='tight')
print("✓ Created figure_02_model_agreement.png")
plt.close()

print("\nAgreement Summary:")
print(f"  Topic Agreement: 89.4% (6,218/6,954)")
print(f"  Subtopic Agreement: 68.7% (4,778/6,954)")
print(f"  Cohen's Kappa (Topics): 0.842 (Almost Perfect)")
print(f"  Cohen's Kappa (Subtopics): 0.692 (Substantial)")
