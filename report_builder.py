#!/usr/bin/env python3
"""
Build pipeline for all reports and deliverables.

Renders Quarto projects, generates visuals, and copies final
deliverables to output/ for git tracking.

Usage:
    python report_builder.py                  # build everything
    python report_builder.py fact_sheet       # build just the fact sheet
    python report_builder.py r01              # build Report 01
    python report_builder.py r02              # build Report 02
    python report_builder.py r03              # build Report 03 (report + slides)
    python report_builder.py r03-report       # build Report 03 report only
    python report_builder.py r03-slides       # build Report 03 slides only
    python report_builder.py r03-visuals      # regenerate Report 03 visuals only
    python report_builder.py list             # show all targets
    python report_builder.py status           # check what exists / what's missing
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# ── Source directories ──────────────────────────────────────────────
SRC = {
    "fact_sheet":  REPO_ROOT / "reports" / "fact_sheet",
    "r01":         REPO_ROOT / "reports" / "01_llm_concept_mapping",
    "r02":         REPO_ROOT / "reports" / "02_question_consolidation",
    "r03_report":  REPO_ROOT / "reports" / "03_harmonization_constraints" / "report",
    "r03_slides":  REPO_ROOT / "reports" / "03_harmonization_constraints" / "presentation",
}

# ── Output destinations (tracked in git) ────────────────────────────
DEST = {
    "fact_sheet":  REPO_ROOT / "output" / "fact_sheet",
    "r01":         REPO_ROOT / "output" / "report_01",
    "r02":         REPO_ROOT / "output" / "report_02",
    "r03_pdf":     REPO_ROOT / "output" / "report_03" / "pdf",
    "r03_visuals": REPO_ROOT / "output" / "report_03" / "visuals",
}

# ── Visual generation scripts ───────────────────────────────────────
VISUAL_SCRIPTS = {
    "r03_base":    REPO_ROOT / "src" / "scripts" / "generate_visuals.py",
    "r03_model":   REPO_ROOT / "src" / "scripts" / "stage4_model_validation_visuals.py",
    "r03_harmdist": REPO_ROOT / "src" / "scripts" / "visualize_harmonization_distribution.py",
    "r03_qdist":   REPO_ROOT / "src" / "scripts" / "visualize_question_consolidation_distribution.py",
}

# ── Copy manifests: (source_glob_in_output_dir, dest_dir, rename) ──
# After quarto render, _output/ has the built files. These map what
# to copy where. rename=None means keep original filename.
COPY_RULES = {
    "fact_sheet": [
        ("index.pdf", DEST["fact_sheet"], "fact_sheet.pdf"),
    ],
    "r01": [
        ("*.pdf", DEST["r01"], None),
    ],
    "r02": [
        ("*.pdf", DEST["r02"], None),
    ],
    "r03_report": [
        ("*.pdf", DEST["r03_pdf"], None),
    ],
    "r03_slides": [
        # RevealJS HTML slides
        ("*.html", DEST["r03_pdf"], None),
    ],
}

# ── Slide images that should be symlinked/copied from visuals ──────
SLIDE_IMAGES_DIR = SRC["r03_slides"] / "images"


def run(cmd, cwd=None, label=""):
    """Run a shell command, print output, return success bool."""
    print(f"\n{'─'*60}")
    print(f"  {label}" if label else f"  {' '.join(cmd)}")
    print(f"  cwd: {cwd or '.'}")
    print(f"{'─'*60}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=False)
    if result.returncode != 0:
        print(f"  ✗ FAILED (exit {result.returncode})")
        return False
    print(f"  ✓ OK")
    return True


def copy_outputs(target_key, src_dir):
    """Copy rendered outputs from _output/ to tracked output/ directory."""
    output_dir = src_dir / "_output"
    if not output_dir.exists():
        print(f"  ⚠ No _output/ directory in {src_dir}")
        return False

    rules = COPY_RULES.get(target_key, [])
    copied = 0
    for glob_pattern, dest_dir, rename in rules:
        dest_dir.mkdir(parents=True, exist_ok=True)
        for src_file in output_dir.glob(glob_pattern):
            if src_file.is_file():
                dest_name = rename if rename else src_file.name
                dest_path = dest_dir / dest_name
                shutil.copy2(src_file, dest_path)
                rel_dest = dest_path.relative_to(REPO_ROOT)
                print(f"  → {rel_dest}")
                copied += 1

    if copied == 0:
        print(f"  ⚠ No files matched copy rules for {target_key}")
        return False
    return True


def sync_slide_images():
    """Ensure presentation/images/ has current visuals.
    
    If images/ is a symlink to the visuals dir, nothing to do.
    Otherwise, copy files over (skip if src == dst).
    """
    src = DEST["r03_visuals"]
    dst = SLIDE_IMAGES_DIR
    if not src.exists():
        print(f"  ⚠ No visuals directory at {src}")
        return False

    # If dst is a symlink pointing to src, we're already in sync
    if dst.is_symlink() or dst.resolve() == src.resolve():
        print(f"  → presentation/images/ already linked to visuals (symlink)")
        return True

    dst.mkdir(parents=True, exist_ok=True)
    copied = 0
    for png in src.glob("*.png"):
        dest_file = dst / png.name
        if dest_file.resolve() == png.resolve():
            continue  # same file, skip
        shutil.copy2(png, dest_file)
        copied += 1
    print(f"  → Synced {copied} images to {dst.relative_to(REPO_ROOT)}")
    return True


def quarto_render(src_dir, label=""):
    """Render a Quarto project and return success."""
    if not (src_dir / "_quarto.yml").exists():
        print(f"  ⚠ No _quarto.yml in {src_dir}")
        return False
    return run(["quarto", "render"], cwd=src_dir, label=label)


# ── Build targets ───────────────────────────────────────────────────

def build_fact_sheet():
    ok = quarto_render(SRC["fact_sheet"], "Rendering fact sheet")
    if ok:
        copy_outputs("fact_sheet", SRC["fact_sheet"])
    return ok


def build_r01():
    ok = quarto_render(SRC["r01"], "Rendering Report 01")
    if ok:
        copy_outputs("r01", SRC["r01"])
    return ok


def build_r02():
    ok = quarto_render(SRC["r02"], "Rendering Report 02")
    if ok:
        copy_outputs("r02", SRC["r02"])
    return ok


def build_r03_visuals():
    """Regenerate Report 03 visualizations from data."""
    print("\n── Generating Report 03 visuals ──")
    DEST["r03_visuals"].mkdir(parents=True, exist_ok=True)
    all_ok = True
    for name, script in VISUAL_SCRIPTS.items():
        if not script.exists():
            print(f"  ⚠ Script not found: {script.relative_to(REPO_ROOT)}")
            all_ok = False
            continue
        ok = run(
            [sys.executable, str(script)],
            cwd=REPO_ROOT,
            label=f"Running {script.relative_to(REPO_ROOT)}",
        )
        if not ok:
            all_ok = False
    # Sync to slide images directory
    sync_slide_images()
    return all_ok


def build_r03_report():
    ok = quarto_render(SRC["r03_report"], "Rendering Report 03 (report)")
    if ok:
        copy_outputs("r03_report", SRC["r03_report"])
    return ok


def build_r03_slides():
    # Ensure images are current before rendering slides
    sync_slide_images()
    ok = quarto_render(SRC["r03_slides"], "Rendering Report 03 (slides)")
    if ok:
        copy_outputs("r03_slides", SRC["r03_slides"])
    return ok


def build_r03():
    v = build_r03_visuals()
    r = build_r03_report()
    s = build_r03_slides()
    return v and r and s


def build_all():
    results = {}
    for name, fn in [
        ("fact_sheet", build_fact_sheet),
        ("r01", build_r01),
        ("r02", build_r02),
        ("r03", build_r03),
    ]:
        results[name] = fn()

    print(f"\n{'═'*60}")
    print("  BUILD SUMMARY")
    print(f"{'═'*60}")
    for name, ok in results.items():
        status = "✓" if ok else "✗"
        print(f"  {status}  {name}")
    print()
    return all(results.values())


def show_status():
    """Check what deliverables exist and what's missing."""
    print(f"\n{'═'*60}")
    print("  DELIVERABLE STATUS")
    print(f"{'═'*60}")

    checks = [
        ("Fact Sheet PDF",        DEST["fact_sheet"] / "fact_sheet.pdf"),
        ("Report 02 PDF",         DEST["r02"] / "FULL_REPORT.pdf"),
        ("Report 03 slides PDF",  DEST["r03_pdf"] / "slides.pdf"),
        ("Report 03 3A slides",   DEST["r03_pdf"] / "slides_3a_findings.pdf"),
        ("Report 03 3B slides",   DEST["r03_pdf"] / "slides_3b_methodology.pdf"),
    ]

    # Check visuals
    expected_visuals = [
        "barrier_distribution.png",
        "consolidation_rates.png",
        "expert_review_load.png",
        "process_flow.png",
        "triage_quadrant.png",
        "rater_agreement_heatmap.png",
        "arbitrator_agreement_heatmap.png",
        "arbitrator_synthesis_rates.png",
        "single_model_risk.png",
        "family_bias_analysis.png",
        "harmonization_distribution.png",
        "question_consolidation_distribution.png",
    ]

    for label, path in checks:
        status = "✓" if path.exists() else "✗ MISSING"
        rel = path.relative_to(REPO_ROOT)
        print(f"  {status:12s}  {label:30s}  {rel}")

    print()
    vis_dir = DEST["r03_visuals"]
    found = 0
    missing = 0
    for v in expected_visuals:
        if (vis_dir / v).exists():
            found += 1
        else:
            missing += 1
            print(f"  ✗ MISSING   R03 visual: {v}")
    if missing == 0:
        print(f"  ✓            All {found} R03 visuals present")
    else:
        print(f"  ⚠            {found}/{found+missing} R03 visuals present, {missing} missing")

    # Check slide images sync
    print()
    slide_img = SLIDE_IMAGES_DIR
    if slide_img.exists():
        n = len(list(slide_img.glob("*.png")))
        print(f"  ℹ            {n} images in presentation/images/")
    else:
        print(f"  ✗ MISSING   presentation/images/ directory")

    print()


def show_targets():
    targets = {
        "all":          "Build everything",
        "fact_sheet":   "Executive fact sheet (PDF)",
        "r01":          "Report 01 — LLM Concept Mapping (PDF + HTML)",
        "r02":          "Report 02 — Question Consolidation (PDF + HTML)",
        "r03":          "Report 03 — full build (visuals + report + slides)",
        "r03-report":   "Report 03 — Quarto report only",
        "r03-slides":   "Report 03 — slides only (syncs images first)",
        "r03-visuals":  "Report 03 — regenerate visuals from data",
        "status":       "Check what deliverables exist",
        "list":         "Show this list",
    }
    print(f"\n{'═'*60}")
    print("  BUILD TARGETS")
    print(f"{'═'*60}")
    for name, desc in targets.items():
        print(f"  {name:16s}  {desc}")
    print(f"\nUsage: python report_builder.py <target>")
    print(f"       python report_builder.py          (builds all)\n")


# ── CLI ─────────────────────────────────────────────────────────────

TARGETS = {
    "all":         build_all,
    "fact_sheet":  build_fact_sheet,
    "r01":         build_r01,
    "r02":         build_r02,
    "r03":         build_r03,
    "r03-report":  build_r03_report,
    "r03-slides":  build_r03_slides,
    "r03-visuals": build_r03_visuals,
    "status":      show_status,
    "list":        show_targets,
}


def main():
    parser = argparse.ArgumentParser(
        description="Build reports and deliverables.",
        usage="python report_builder.py [target]",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        choices=list(TARGETS.keys()),
        help="Build target (default: all)",
    )
    args = parser.parse_args()

    result = TARGETS[args.target]()

    if isinstance(result, bool) and not result:
        sys.exit(1)


if __name__ == "__main__":
    main()
