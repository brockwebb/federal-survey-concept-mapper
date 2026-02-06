#!/usr/bin/env python3
"""
Generate Figure 1: Methodology Flow Diagram
Converts the Mermaid pipeline diagram to a clean visualization.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# Create figure
fig, ax = plt.subplots(figsize=(14, 10))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Colors
color_start = '#e1f5e1'
color_cat = '#fff3cd'
color_analysis = '#cfe2ff'
color_arb = '#f8d7da'
color_final = '#d1ecf1'

# Box dimensions
box_width = 8
box_height = 1.2
x_center = 5

# Helper function to draw boxes
def draw_box(ax, x, y, width, height, text, color, text_size=11):
    box = FancyBboxPatch(
        (x - width/2, y - height/2),
        width, height,
        boxstyle="round,pad=0.1",
        edgecolor='black',
        facecolor=color,
        linewidth=2
    )
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=text_size, 
            fontweight='bold', wrap=True)

# Helper function to draw arrows
def draw_arrow(ax, x1, y1, x2, y2):
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle='->,head_width=0.4,head_length=0.4',
        color='black',
        linewidth=2,
        mutation_scale=20
    )
    ax.add_patch(arrow)

# Draw boxes (top to bottom)
y_positions = [11, 9.2, 7.4, 5.6, 3.8, 2.0, 0.5]

# Start
draw_box(ax, x_center, y_positions[0], box_width, box_height,
         'Raw Survey Questions\n6,987 questions from 46 federal surveys',
         color_start, 12)

# Step 1
draw_box(ax, x_center, y_positions[1], box_width, box_height,
         'Step 1: Claude Haiku 4.5 Categorization\nSerial execution (runs FIRST)\n~12 minutes',
         color_cat, 10)

# Step 2
draw_box(ax, x_center, y_positions[2], box_width, box_height,
         'Step 2: GPT-5-mini Categorization\nSerial execution (runs SECOND)\n~67 minutes',
         color_cat, 10)

# Step 3
draw_box(ax, x_center, y_positions[3], box_width, box_height,
         'Step 3: Agreement Analysis\nCohen\'s Kappa, Confidence Tiers\n<1 minute',
         color_analysis, 10)

# Step 4
draw_box(ax, x_center, y_positions[4], box_width, box_height,
         'Step 4: Disagreement Stratification\n4 confidence tiers (very_low → high)\n<1 minute',
         color_analysis, 10)

# Step 5
draw_box(ax, x_center, y_positions[5], box_width, box_height,
         'Step 5: Arbitration (Claude Sonnet 4.5)\nSingle-pass arbitration + auto dual-modal\n~52 minutes',
         color_arb, 10)

# Step 6
draw_box(ax, x_center, y_positions[6], box_width, box_height,
         'Step 6: Final Reconciliation\nMaster Dataset (6,987 questions)\n<1 minute',
         color_final, 10)

# Draw arrows
for i in range(len(y_positions) - 1):
    draw_arrow(ax, x_center, y_positions[i] - box_height/2 - 0.05,
               x_center, y_positions[i+1] + box_height/2 + 0.05)

# Add title
ax.text(x_center, 11.8, 'Federal Survey Concept Mapping Pipeline',
        ha='center', va='top', fontsize=16, fontweight='bold')

# Add subtitle
ax.text(x_center, -0.3, 'Total Runtime: ~3 hours | Total Cost: ~$15 | Success Rate: 99.5%',
        ha='center', va='top', fontsize=12, style='italic')

# Add note about serial execution
note_box = FancyBboxPatch(
    (0.2, 7.0), 2.5, 1.0,
    boxstyle="round,pad=0.1",
    edgecolor='red',
    facecolor='#ffe6e6',
    linewidth=2,
    linestyle='--'
)
ax.add_patch(note_box)
ax.text(1.45, 7.5, 'SERIAL\nEXECUTION',
        ha='center', va='center', fontsize=9, fontweight='bold', color='red')

plt.tight_layout()
plt.savefig('../final_report/figures/figure_01_methodology_flow.png', dpi=300, bbox_inches='tight')
print("✓ Created figure_01_methodology_flow.png")
plt.close()
