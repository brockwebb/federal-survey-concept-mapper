#!/usr/bin/env python3
"""Build the v2 results report PDF.

DEV-only build tooling (Quarto is the project report build system; it is
not installed on WORK, so this script intentionally does not follow the
WORK in-process-import rule -- there is nothing to import, quarto is a
CLI).

Usage, from anywhere:
    python v2/report/build_report_pdf.py

Renders v2_results_report.qmd to v2_results_report.pdf in this directory.
Exits nonzero if quarto fails or the PDF does not appear.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
QMD = HERE / "v2_results_report.qmd"
PDF = QMD.with_suffix(".pdf")


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if shutil.which("quarto") is None:
        die("quarto not found on PATH. This is DEV build tooling; "
            "install quarto or run on the DEV machine.")
    if not QMD.exists():
        die(f"source not found: {QMD}")

    result = subprocess.run(
        ["quarto", "render", str(QMD.name), "--to", "pdf"],
        cwd=HERE,
    )
    if result.returncode != 0:
        die(f"quarto render exited {result.returncode}")
    if not PDF.exists():
        die("quarto exited 0 but no PDF was produced")

    print(f"PDF: {PDF}")


if __name__ == "__main__":
    main()
