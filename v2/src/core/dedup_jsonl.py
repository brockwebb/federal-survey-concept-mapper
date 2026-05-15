#!/usr/bin/env python3
"""Deduplicate Stage 1 JSONL result files.

The retry path in stage1_classify.py appends recovered records to the
existing JSONL without removing the original (truncated/failed) entries.
This produces duplicate IDs. This script deduplicates on the `id` field,
keeping the LAST occurrence (the retry's clean record overwrites the
original's broken one).

Run from v2/ directory:

    # Dry run (report only, no changes):
    python src/core/dedup_jsonl.py

    # Apply dedup (overwrites in place, backup created):
    python src/core/dedup_jsonl.py --apply

    # Target a specific file instead of auto-discovering:
    python src/core/dedup_jsonl.py --file output/stage1/results_rater_b_gemini-2_5-flash.jsonl --apply

Reads output paths from config/stage1.yaml so nothing is hardcoded.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_PATH = Path("config/stage1.yaml")


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        print(f"ERROR: Config not found at {CONFIG_PATH.resolve()}. "
              f"Run from the v2/ directory.", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def discover_jsonl_files(cfg: dict) -> list[Path]:
    """Find all Stage 1 result JSONL files from config-derived output dir."""
    output_dir = Path(cfg["output"]["output_dir"])
    if not output_dir.exists():
        print(f"ERROR: Output dir {output_dir.resolve()} does not exist.",
              file=sys.stderr)
        sys.exit(1)
    return sorted(output_dir.glob("results_*.jsonl"))


def dedup_jsonl(path: Path, apply: bool) -> dict:
    """Deduplicate a JSONL file on `id`, last-write-wins.

    Returns a summary dict with before/after counts and duplicate IDs.
    """
    lines = path.read_text(encoding="utf-8").strip().split("\n")
    lines = [l for l in lines if l.strip()]  # drop blank lines

    seen: dict[str, str] = {}
    duplicate_ids: list[str] = []

    for line in lines:
        rec = json.loads(line)
        rec_id = str(rec["id"])
        if rec_id in seen:
            duplicate_ids.append(rec_id)
        seen[rec_id] = line  # last write wins

    summary = {
        "file": str(path),
        "before": len(lines),
        "after": len(seen),
        "duplicates_removed": len(lines) - len(seen),
        "duplicate_ids": duplicate_ids,
    }

    if apply and duplicate_ids:
        # Backup original
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = path.with_suffix(f".pre_dedup_{ts}.jsonl.bak")
        shutil.copy2(path, backup)
        summary["backup"] = str(backup)

        # Write deduped
        path.write_text(
            "\n".join(seen.values()) + "\n",
            encoding="utf-8",
        )

    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deduplicate Stage 1 JSONL result files (last-write-wins on id)."
    )
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually overwrite files. Without this flag, dry-run only.",
    )
    parser.add_argument(
        "--file", type=Path, default=None,
        help="Target a specific JSONL file instead of auto-discovering all.",
    )
    args = parser.parse_args()

    cfg = load_config()

    if args.file:
        if not args.file.exists():
            print(f"ERROR: {args.file} does not exist.", file=sys.stderr)
            return 1
        targets = [args.file]
    else:
        targets = discover_jsonl_files(cfg)

    if not targets:
        print("No JSONL files found.")
        return 0

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"=== Stage 1 JSONL Dedup ({mode}) ===\n")

    any_dupes = False
    for path in targets:
        result = dedup_jsonl(path, apply=args.apply)
        status = "CLEAN" if result["duplicates_removed"] == 0 else "DUPES FOUND"
        print(f"  {path.name}: {status}")
        print(f"    Before: {result['before']}  After: {result['after']}  "
              f"Removed: {result['duplicates_removed']}")
        if result["duplicate_ids"]:
            any_dupes = True
            print(f"    Duplicate IDs: {result['duplicate_ids']}")
        if "backup" in result:
            print(f"    Backup: {result['backup']}")
        print()

    if any_dupes and not args.apply:
        print("Re-run with --apply to fix.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
