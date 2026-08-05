#!/usr/bin/env python3
"""
build.py — Assemble article.qmd from source files and optionally render.

Source of truth:
  - frontmatter.yml    (YAML config)
  - abstract.md        (abstract text)
  - chapters/*.qmd     (chapter content)
  - appendices/*.qmd   (appendix content)

Output:
  - article.qmd (build artifact — do NOT edit directly)

Usage:
  python build.py              # assemble article.qmd
  python build.py --render     # assemble + quarto render
  python build.py --open       # assemble + render + open PDF
  python build.py --validate   # run validation before assembly
"""

import os
import re
import sys
import subprocess
from pathlib import Path

# --- Configuration (derived from file system, not hardcoded) ---

PROJECT_DIR = Path(__file__).parent
OUTPUT_FILE = PROJECT_DIR / "article.qmd"

FRONTMATTER = PROJECT_DIR / "frontmatter.yml"
ABSTRACT = PROJECT_DIR / "abstract.md"

CHAPTERS = [
    PROJECT_DIR / "chapters" / "01_introduction.qmd",
    PROJECT_DIR / "chapters" / "02_classification.qmd",
    PROJECT_DIR / "chapters" / "03_survey_overlap.qmd",
    PROJECT_DIR / "chapters" / "04_pairwise_harmonization.qmd",
    PROJECT_DIR / "chapters" / "05_results.qmd",
    PROJECT_DIR / "chapters" / "06_implications.qmd",
    PROJECT_DIR / "chapters" / "07_limitations.qmd",
]

APPENDICES = [
    PROJECT_DIR / "appendices" / "A_architecture.qmd",
    PROJECT_DIR / "appendices" / "B_taxonomy.qmd",
    PROJECT_DIR / "appendices" / "C_tevv.qmd",
]

VALIDATION_SCRIPT = PROJECT_DIR.parent / "src" / "validation" / "validate_complete.py"


# Architecture diagrams: source → report/figures/ symlinks
DIAGRAM_SOURCE = PROJECT_DIR.parent / "assets" / "diagrams"
DIAGRAM_DEST = PROJECT_DIR / "figures"
DIAGRAMS = [
    "fig_pipeline_overview.png",
    "fig_stage1_classification.png",
    "fig_stage2_overlap.png",
    "fig_stage3_rating.png",
    "fig_stage4_arbitration.png",
]


def sync_diagrams():
    """Ensure architecture diagrams are symlinked into report/figures/."""
    DIAGRAM_DEST.mkdir(parents=True, exist_ok=True)
    for name in DIAGRAMS:
        src = DIAGRAM_SOURCE / name
        dst = DIAGRAM_DEST / name
        if dst.is_symlink() or dst.exists():
            dst.unlink()  # refresh
        if src.exists():
            # Relative, not absolute: these symlinks are committed, so an
            # absolute target bakes in this machine's checkout path and breaks
            # every other clone (the previously committed links still pointed at
            # a ~/Documents/GitHub location that no longer exists).
            dst.symlink_to(os.path.relpath(src.resolve(), dst.parent.resolve()))
        else:
            print(f"WARNING: diagram source missing: {src}", file=sys.stderr)


def validate_sources():
    """Check all source files exist before assembly."""
    missing = []
    for f in [FRONTMATTER, ABSTRACT] + CHAPTERS + APPENDICES:
        if not f.exists():
            missing.append(str(f.name))
    if missing:
        print(f"ERROR: Missing source files: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)


def run_validation():
    """Run the validation suite."""
    if not VALIDATION_SCRIPT.exists():
        print(f"WARNING: Validation script not found: {VALIDATION_SCRIPT}", file=sys.stderr)
        return True
    print("Running validation...")
    result = subprocess.run(
        [sys.executable, str(VALIDATION_SCRIPT)],
        cwd=PROJECT_DIR.parent,
    )
    if result.returncode == 1:
        print("ERROR: Validation FAILED. Fix issues before rendering.", file=sys.stderr)
        sys.exit(1)
    elif result.returncode == 2:
        print("WARNING: Validation passed with warnings.", file=sys.stderr)
    else:
        print("Validation passed.")
    return True


def prepare_appendix(text):
    """Add {.unnumbered} to appendix headings that don't already have it."""
    lines = text.split("\n")
    result = []
    for line in lines:
        if re.match(r'^#{1,6}\s', line) and '{.unnumbered}' not in line:
            line = line.rstrip() + " {.unnumbered}"
        result.append(line)
    return "\n".join(result)


def assemble():
    """Assemble article.qmd from source files."""
    validate_sources()

    parts = []

    # --- YAML front matter ---
    parts.append("---")
    parts.append(FRONTMATTER.read_text().rstrip())

    # Inject abstract (indented 2 spaces for YAML block scalar)
    abstract_text = ABSTRACT.read_text().rstrip()
    abstract_indented = "\n".join(
        f"  {line}" if line.strip() else ""
        for line in abstract_text.splitlines()
    )
    parts.append(f"abstract: |\n{abstract_indented}")

    parts.append("---")

    # --- Chapter content ---
    for ch in CHAPTERS:
        parts.append("")  # blank line separator
        parts.append(ch.read_text().rstrip())

    # --- References ---
    parts.append("")
    parts.append("# References {.unnumbered}")
    parts.append("")
    parts.append("::: {#refs}")
    parts.append(":::")

    # --- Appendices ---
    for app in APPENDICES:
        parts.append("")
        parts.append(prepare_appendix(app.read_text().rstrip()))

    # --- Write output ---
    assembled = "\n".join(parts) + "\n"
    OUTPUT_FILE.write_text(assembled)

    line_count = assembled.count("\n")
    print(f"Assembled {OUTPUT_FILE.name} ({line_count} lines) from {len(CHAPTERS)} chapters + {len(APPENDICES)} appendices")


def render():
    """Run quarto render on the assembled article."""
    print("Rendering PDF...")
    result = subprocess.run(
        ["quarto", "render", str(OUTPUT_FILE)],
        cwd=PROJECT_DIR,
    )
    if result.returncode != 0:
        print("ERROR: quarto render failed", file=sys.stderr)
        sys.exit(1)
    print("Done: _output/article.pdf")


def copy_output():
    """Copy rendered PDF to report directory with friendly name."""
    src = PROJECT_DIR / "_output" / "article.pdf"
    dst = PROJECT_DIR / "FedSurveyHarmonization.pdf"
    if src.exists():
        import shutil
        shutil.copy2(src, dst)
        print(f"Copied: {dst}")
    else:
        print(f"WARNING: {src} not found, skipping copy", file=sys.stderr)


def open_pdf():
    """Open the rendered PDF."""
    pdf_path = PROJECT_DIR / "FedSurveyHarmonization.pdf"
    if not pdf_path.exists():
        pdf_path = PROJECT_DIR / "_output" / "article.pdf"
    if pdf_path.exists():
        subprocess.run(["open", str(pdf_path)])
    else:
        print(f"ERROR: No PDF found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if "--validate" in sys.argv:
        run_validation()

    sync_diagrams()
    assemble()

    if "--render" in sys.argv or "--open" in sys.argv:
        render()
        copy_output()

    if "--open" in sys.argv:
        open_pdf()
