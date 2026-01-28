#!/usr/bin/env python3
"""Render Mermaid diagrams to PNG using mermaid-cli (mmdc).

Install: npm install -g @mermaid-js/mermaid-cli
"""

import subprocess
import sys
from pathlib import Path


def check_mmdc() -> bool:
    """Check if mmdc is available."""
    try:
        subprocess.run(["mmdc", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def render_diagram(mmd_file: Path, output_file: Path):
    """Render a single Mermaid diagram to PNG."""
    subprocess.run([
        "mmdc",
        "-i", str(mmd_file),
        "-o", str(output_file),
        "-b", "white",
        "-w", "1200",
        "-H", "800"
    ], check=True)


def main():
    """Render all Mermaid diagrams."""
    base = Path(__file__).parent.parent
    diagrams_dir = base / "diagrams"
    figures_dir = base / "figures"
    
    # Check mmdc is available
    if not check_mmdc():
        print("✗ mmdc not found")
        print("  Install with: npm install -g @mermaid-js/mermaid-cli")
        sys.exit(1)
    
    figures_dir.mkdir(exist_ok=True)
    
    # Find all .mmd files
    mmd_files = list(diagrams_dir.glob("*.mmd"))
    
    if not mmd_files:
        print(f"  No .mmd files found in {diagrams_dir}")
        return
    
    print(f"Rendering {len(mmd_files)} diagrams...")
    
    for mmd_file in mmd_files:
        output_file = figures_dir / f"{mmd_file.stem}.png"
        print(f"  {mmd_file.name} → {output_file.name}")
        try:
            render_diagram(mmd_file, output_file)
        except subprocess.CalledProcessError as e:
            print(f"    ✗ Failed: {e}")
    
    print(f"Done: {len(mmd_files)} diagrams rendered to {figures_dir}")


if __name__ == "__main__":
    main()
