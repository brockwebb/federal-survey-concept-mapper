#!/usr/bin/env python3
"""Build all v2 report PDFs.

DEV-only build tooling (Quarto is the project report build system; not on
WORK). Renders every .qmd in this directory to PDF.

Usage, from anywhere:
    python v2/report/build_report_pdf.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if shutil.which("quarto") is None:
        die("quarto not found on PATH. This is DEV build tooling; "
            "install quarto or run on the DEV machine.")

    qmds = sorted(HERE.glob("*.qmd"))
    if not qmds:
        die(f"no .qmd files in {HERE}")

    failures = []
    for qmd in qmds:
        result = subprocess.run(
            ["quarto", "render", qmd.name, "--to", "pdf"],
            cwd=HERE,
        )
        pdf = qmd.with_suffix(".pdf")
        if result.returncode != 0 or not pdf.exists():
            failures.append(qmd.name)
        else:
            print(f"PDF: {pdf}")

    if failures:
        die(f"render failed for: {', '.join(failures)}")


if __name__ == "__main__":
    main()
