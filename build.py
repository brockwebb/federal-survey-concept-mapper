#!/usr/bin/env python3
"""
Validation-gated build script for the master report.

Usage:
    python build.py              # validate + render report
    python build.py --validate   # validate only (no render)
    python build.py --force      # render without validation (escape hatch)
    python build.py --figures    # regenerate figures, then validate + render
"""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
REPORT_DIR = REPO / "report"
VALIDATE_SCRIPT = REPO / "src" / "validation" / "validate_complete.py"

# Figure scripts in generation order (from SCRIPT_ARTIFACT_MAP)
FIGURE_SCRIPTS = [
    REPO / "src" / "figures" / "fig01_topic_distribution.py",
    REPO / "src" / "figures" / "fig02_acs_family_profile.py",
    REPO / "src" / "figures" / "fig03_paired_topic_composition.py",
    REPO / "src" / "scripts" / "generate_visuals.py",
    REPO / "src" / "scripts" / "stage4_model_validation_visuals.py",
    REPO / "src" / "scripts" / "visualize_harmonization_distribution.py",
    REPO / "src" / "scripts" / "visualize_question_consolidation_distribution.py",
]


def run(cmd, cwd=None, capture=False):
    """Run a command and return (returncode, stdout+stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=capture,
        text=True,
    )
    return result.returncode, result.stdout + result.stderr if capture else ""


def step_figures():
    """Regenerate all figure outputs."""
    print("=" * 60)
    print("FIGURE REGENERATION")
    print("=" * 60)
    failed = []
    for script in FIGURE_SCRIPTS:
        if not script.exists():
            print(f"  [SKIP] {script.name} — file not found")
            continue
        print(f"  Running {script.name}...")
        rc, _ = run([sys.executable, str(script)], cwd=REPO)
        if rc == 0:
            print(f"  [OK]   {script.name}")
        else:
            print(f"  [FAIL] {script.name} — exit {rc}")
            failed.append(script.name)
    if failed:
        print(f"\nFigure generation failed for: {', '.join(failed)}")
        return False
    print("\nAll figures regenerated.")
    return True


def step_validate():
    """Run the validation suite. Returns True if all checks pass."""
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)
    rc, _ = run([sys.executable, str(VALIDATE_SCRIPT)], cwd=REPO)
    if rc == 0:
        print("\nValidation: PASS (all checks pass)")
        return True
    else:
        print(f"\nValidation: FAIL (exit code {rc})")
        print("Review validation output above. Refusing to render.")
        return False


def step_render():
    """Run quarto render from the report directory."""
    print("=" * 60)
    print("QUARTO RENDER")
    print("=" * 60)
    rc, _ = run(["quarto", "render"], cwd=REPORT_DIR)
    if rc == 0:
        output_dir = REPORT_DIR / "_output"
        print(f"\nRender: OK — output at {output_dir}")
        return True
    else:
        print(f"\nRender: FAIL (exit code {rc})")
        return False


def main():
    args = set(sys.argv[1:])
    validate_only = "--validate" in args
    force = "--force" in args
    regen_figures = "--figures" in args

    results = {}

    # Figure regeneration (before validation so fresh outputs are validated)
    if regen_figures:
        ok = step_figures()
        results["figures"] = "OK" if ok else "FAIL"
        if not ok:
            _summary(results)
            sys.exit(1)

    # Validate-only mode
    if validate_only:
        ok = step_validate()
        results["validation"] = "PASS" if ok else "FAIL"
        _summary(results)
        sys.exit(0 if ok else 1)

    # Force mode: skip validation, render with loud warning
    if force:
        print("=" * 60)
        print("WARNING: BUILDING WITHOUT VALIDATION — numbers may be stale")
        print("=" * 60)
        results["validation"] = "SKIPPED (--force)"
        ok = step_render()
        results["render"] = "OK" if ok else "FAIL"
        _summary(results)
        sys.exit(0 if ok else 1)

    # Default: validate then render
    ok = step_validate()
    results["validation"] = "PASS" if ok else "FAIL"
    if not ok:
        _summary(results)
        sys.exit(1)

    ok = step_render()
    results["render"] = "OK" if ok else "FAIL"
    _summary(results)
    sys.exit(0 if ok else 1)


def _summary(results):
    print("\n" + "=" * 60)
    print("BUILD SUMMARY")
    print("=" * 60)
    for step, status in results.items():
        print(f"  {step:20s}: {status}")
    print("=" * 60)


if __name__ == "__main__":
    main()
