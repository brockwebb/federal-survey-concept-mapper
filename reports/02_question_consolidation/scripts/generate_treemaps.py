#!/usr/bin/env python3
"""Generate static treemap PNGs for survey-ACS overlap visualization."""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import squarify
from pathlib import Path

# Domain colors (consistent across all treemaps)
DOMAIN_COLORS = {
    "Economic": "#2ecc71",    # Green
    "Social": "#9b59b6",      # Purple
    "Housing": "#3498db",     # Blue
    "Demographic": "#e74c3c"  # Red
}

def load_treemap_data(json_path: Path) -> dict:
    """Load treemap JSON data."""
    with open(json_path) as f:
        return json.load(f)

def flatten_for_squarify(data: dict) -> tuple:
    """Flatten hierarchical data for squarify.
    
    Returns: (sizes, labels, colors, domains)
    """
    sizes = []
    labels = []
    colors = []
    domains = []
    
    for domain in data["children"]:
        domain_name = domain["name"]
        domain_color = DOMAIN_COLORS.get(domain_name, "#95a5a6")
        
        for subtopic in domain["children"]:
            sizes.append(subtopic["value"])
            labels.append(f"{subtopic['name']}\n({subtopic['value']})")
            colors.append(domain_color)
            domains.append(domain_name)
    
    return sizes, labels, colors, domains

def generate_treemap(json_path: Path, output_path: Path, title: str):
    """Generate a treemap PNG from JSON data."""
    data = load_treemap_data(json_path)
    sizes, labels, colors, domains = flatten_for_squarify(data)
    
    # Calculate total
    total = sum(sizes)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))
    fig.patch.set_facecolor('white')
    
    # Generate treemap
    squarify.plot(
        sizes=sizes,
        label=labels,
        color=colors,
        alpha=0.8,
        ax=ax,
        text_kwargs={'fontsize': 8, 'wrap': True}
    )
    
    # Title
    ax.set_title(f"{title} ({total} questions)", fontsize=16, fontweight='bold', pad=20)
    ax.axis('off')
    
    # Legend
    legend_patches = [
        mpatches.Patch(color=color, label=domain, alpha=0.8)
        for domain, color in DOMAIN_COLORS.items()
    ]
    ax.legend(
        handles=legend_patches,
        loc='upper left',
        bbox_to_anchor=(0, -0.02),
        ncol=4,
        fontsize=10
    )
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Generated: {output_path}")

def main():
    """Generate all treemaps."""
    base = Path(__file__).parent.parent
    data_dir = base / "data"
    figures_dir = base / "figures"
    
    treemaps = [
        ("treemap_data_foodaps.json", "treemap_foodaps.png", "FoodAPS-ACS Concept Overlap"),
        ("treemap_data_cps.json", "treemap_cps.png", "CPS-ACS Concept Overlap"),
    ]
    
    for json_file, png_file, title in treemaps:
        json_path = data_dir / json_file
        if json_path.exists():
            generate_treemap(json_path, figures_dir / png_file, title)
        else:
            print(f"Warning: {json_path} not found")

if __name__ == "__main__":
    main()
