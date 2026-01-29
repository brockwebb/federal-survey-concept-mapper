#!/usr/bin/env python3
"""
Build script for Question-Level Survey Consolidation Analysis Report.

Usage:
    python build.py              # Full build (data + figures + assemble + pdf)
    python build.py --data       # Copy data only
    python build.py --figures    # Generate figures only
    python build.py --assemble   # Assemble FULL_REPORT.md only
    python build.py --pdf        # Generate PDF only

Dependencies:
    pip install squarify matplotlib        # For treemap generation
    npm install -g @mermaid-js/mermaid-cli # For mermaid diagrams
    npm install -g md-to-pdf               # For PDF generation
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
SECTIONS_DIR = BASE_DIR / "sections"
FIGURES_DIR = BASE_DIR / "figures"
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"

# Data files to copy (destination: source)
DATA_SOURCES = {
    # From output/visualizations
    "acs_family2_summary.csv": PROJECT_ROOT / "output/visualizations/acs_family2_summary.csv",
    "acs_family2_overlap.csv": PROJECT_ROOT / "output/visualizations/acs_family2_overlap.csv",
    "treemap_data_foodaps.json": PROJECT_ROOT / "output/visualizations/treemap_data_foodaps.json",
    "treemap_data_cps.json": PROJECT_ROOT / "output/visualizations/treemap_data_cps.json",
    # From output/question_matching
    "foodaps_comparison_merged.csv": PROJECT_ROOT / "output/question_matching/foodaps/foodaps_comparison_merged.csv",
    "cps_comparison_merged.csv": PROJECT_ROOT / "output/question_matching/cps/cps_comparison_merged.csv",
}

def ensure_dirs():
    """Create required directories."""
    for d in [SECTIONS_DIR, FIGURES_DIR, DATA_DIR, SCRIPTS_DIR]:
        d.mkdir(exist_ok=True)
    print("✓ Directories ready")

def copy_data():
    """Copy source data into data/ for portability."""
    print("\n=== Copying Data ===")
    copied = 0
    missing = 0
    for dest_name, src_path in DATA_SOURCES.items():
        dest_path = DATA_DIR / dest_name
        if src_path.exists():
            shutil.copy2(src_path, dest_path)
            print(f"  ✓ {dest_name}")
            copied += 1
        else:
            print(f"  ✗ {dest_name} - source not found: {src_path}")
            missing += 1
    print(f"\nCopied: {copied}, Missing: {missing}")

def generate_figures():
    """Generate all figures."""
    print("\n=== Generating Figures ===")
    
    # Generate treemaps
    treemap_script = SCRIPTS_DIR / "generate_treemaps.py"
    if treemap_script.exists():
        print("\nRunning generate_treemaps.py...")
        result = subprocess.run([sys.executable, str(treemap_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    else:
        print(f"  ✗ {treemap_script} not found")
    
    # Generate Mermaid diagrams
    mermaid_script = SCRIPTS_DIR / "render_mermaid.py"
    if mermaid_script.exists():
        print("\nRunning render_mermaid.py...")
        result = subprocess.run([sys.executable, str(mermaid_script)], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
    else:
        print(f"  ✗ {mermaid_script} not found")

def assemble_report():
    """Assemble sections into FULL_REPORT.md."""
    print("\n=== Assembling Report ===")
    
    # Get sections in order (sorted by filename)
    sections = sorted(SECTIONS_DIR.glob("*.md"))
    
    if not sections:
        print("  ✗ No sections found in sections/")
        return
    
    # Header
    header = f"""# Question-Level Survey Consolidation Analysis

**Federal Survey Concept Mapper Project**

*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

---

**Table of Contents**

"""
    
    # Build TOC
    toc_lines = []
    for i, section_path in enumerate(sections, 1):
        # Extract first H1 or H2 from section for TOC
        content = section_path.read_text()
        title = section_path.stem.replace("_", " ").title()
        for line in content.split("\n"):
            if line.startswith("# "):
                title = line[2:].strip()
                break
            elif line.startswith("## ") and not title:
                title = line[3:].strip()
                break
        toc_lines.append(f"{i}. {title}")
    
    toc = "\n".join(toc_lines) + "\n\n---\n\n"
    
    # Assemble
    output_path = BASE_DIR / "FULL_REPORT.md"
    with open(output_path, "w") as out:
        out.write(header)
        out.write(toc)
        
        for section_path in sections:
            print(f"  Adding: {section_path.name}")
            content = section_path.read_text()
            out.write(content)
            out.write("\n\n---\n\n")
    
    print(f"\n✓ Assembled: {output_path}")
    print(f"  Sections: {len(sections)}")

def check_command(cmd: str) -> bool:
    """Check if a command is available."""
    try:
        subprocess.run([cmd, "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_pdf():
    """Generate PDF from assembled report using md-to-pdf.
    
    Uses md-to-pdf (npm package) which renders via Puppeteer/Chrome.
    Much more reliable than weasyprint for complex markdown.
    
    Install: npm install -g md-to-pdf
    """
    print("\n=== Generating PDF ===")
    
    input_path = BASE_DIR / "FULL_REPORT.md"
    output_path = BASE_DIR / "FULL_REPORT.pdf"
    config_path = SCRIPTS_DIR / "pdf-config.json"
    
    if not input_path.exists():
        print("  ✗ FULL_REPORT.md not found - run --assemble first")
        return
    
    if not check_command("md-to-pdf"):
        print("  ✗ md-to-pdf not found")
        print("  Install with: npm install -g md-to-pdf")
        return
    
    print(f"  {input_path.name} → {output_path.name}")
    
    try:
        cmd = ["md-to-pdf", str(input_path)]
        if config_path.exists():
            cmd.extend(["--config-file", str(config_path)])
        
        # Run from BASE_DIR for relative image paths
        subprocess.run(cmd, check=True, cwd=BASE_DIR)
        print(f"✓ Generated: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ PDF generation failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Build question-level analysis report")
    parser.add_argument("--data", action="store_true", help="Copy data only")
    parser.add_argument("--figures", action="store_true", help="Generate figures only")
    parser.add_argument("--assemble", action="store_true", help="Assemble report only")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF only")
    args = parser.parse_args()
    
    # If no flags, build everything. If any flag, only that step.
    do_all = not (args.data or args.figures or args.assemble or args.pdf)
    
    print("=" * 50)
    print("Question-Level Analysis Report Builder")
    print("=" * 50)
    
    ensure_dirs()
    
    if do_all or args.data:
        copy_data()
    
    if do_all or args.figures:
        generate_figures()
    
    if do_all or args.assemble:
        assemble_report()
    
    if do_all or args.pdf:
        generate_pdf()
    
    print("\n" + "=" * 50)
    print("Build Complete")
    print("=" * 50)

if __name__ == "__main__":
    main()
