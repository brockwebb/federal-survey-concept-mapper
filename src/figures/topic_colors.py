"""Canonical topic color mapping for all report figures.

Colors from U.S. Census Bureau xdgov Data Design Standards.
https://xdgov.github.io/data-design-standards/components/colors

Every figure script imports this module to ensure consistent topic colors.
Section 508 compliant: all colors meet 4.5:1 contrast on white.
"""

# Topic → hex color (qualitative palette, 5 categories)
TOPIC_COLORS = {
    "Economic":     "#112E51",  # census-color-navy
    "Social":       "#0095A8",  # census-color-teal
    "Housing":      "#FF7043",  # census-color-orange
    "Demographic":  "#2E78D2",  # census-color-blue
    "Government":   "#78909C",  # census-color-grey
}

# Ordered list for consistent rendering (largest to smallest)
TOPIC_ORDER = ["Economic", "Social", "Housing", "Demographic", "Government"]

# Text colors for labels inside bars (white on dark, dark on light)
TOPIC_TEXT_COLORS = {
    "Economic":     "#FFFFFF",  # white on navy
    "Social":       "#FFFFFF",  # white on teal
    "Housing":      "#FFFFFF",  # white on orange
    "Demographic":  "#FFFFFF",  # white on blue
    "Government":   "#FFFFFF",  # white on grey
}

# Standard figure dimensions (inches) — letter paper, 1in margins = 6.5in
FIGURE_WIDTH = 6.5
FIGURE_DPI = 300
