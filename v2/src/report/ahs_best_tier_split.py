#!/usr/bin/env python3
"""AHS best-tier split on the unique-question unit.

Fills the two `pending` cells in
`v2/report/three_survey_harmonization_summary.qmd`: of the AHS questions that
have at least one harmonization candidate into ACS, how many are best-tier F1
and how many are best-tier F2.

WHY THIS SCRIPT EXISTS
----------------------
`stage3_ahs_rollup.py` reports F1/F2 counts as PAIR counts (71 F1 pairs, 59 F2
pairs). Those are a different unit from questions and are not substitutes: one
AHS question pairs against several ACS questions sharing a subtopic, so a
question can contribute an F1 pair and an F2 pair at the same time. The
three-survey summary reports CPS and FoodAPS on the question unit, so AHS must
match. This script collapses the candidate pair set onto the question and
assigns each question its best tier.

BEST TIER RULE
--------------
F1 if any of the question's candidate pairs is F1, else F2. `ahs_candidates.csv`
holds candidates only (the rollup writes the F1/F2 subset), so every question
present has at least one F1 or F2 pair and the two buckets partition the set.
A feasibility outside {F1, F2} means the input is not the candidates file we
think it is, so we fail rather than guess.

GROUPING UNIT: QUESTION TEXT, NOT ID
------------------------------------
Grouping is on `survey_text`, the unique question text, consistent with the
project dedup rule (`validate_question_counts.py` dedups on full question text,
not on the question id, because dual-subtopic classification assigns multiple
ids to one text). `survey_q_id` is counted alongside as a diagnostic only.

The unique-text count is asserted equal to
`question_level.unique_ahs_questions_with_candidate` in
`ahs_candidate_summary.json`, which the rollup computed by collapsing on
`survey_q_id`. If the two disagree, some AHS question text carries more than
one id and the summary's 92 is an id count rather than a text count. That is a
finding, not a rounding difference, so the mismatch hard-fails with both
numbers and the offending texts printed.

Run from v2/ (the AHS data lives on WORK only; authored on DEV, run on WORK):
    python src/report/ahs_best_tier_split.py
    python src/report/ahs_best_tier_split.py --ahs-dir output/stage3/results/ahs
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

# =============================================================================
# CONSTANTS / PATHS (defaults assume cwd == v2/, mirroring stage3_ahs_rollup.py)
# =============================================================================

DEFAULT_AHS_DIR = Path("output/stage3/results/ahs")
CANDIDATES_NAME = "ahs_candidates.csv"
SUMMARY_NAME = "ahs_candidate_summary.json"

# Columns this script reads. Written by candidate_frame() in
# stage3_ahs_rollup.py; a missing column means the input is not that file.
REQUIRED_COLUMNS = ["pair_id", "survey_q_id", "final_feasibility", "survey_text"]

# The candidates file is the F1/F2 subset by construction. Anything else present
# is a defect in the upstream rollup, not a case to handle silently.
CANDIDATE_FEAS = ("F1", "F2")

# Where the expected unique-question count is read from. Nested under
# question_level by build_question_level(); the top level is accepted as a
# fallback so a future flattening of the summary does not silently skip the
# check.
EXPECTED_KEY = "unique_ahs_questions_with_candidate"
EXPECTED_PARENT = "question_level"

# CSV fields carry full question text; the default 128 KB field limit is ample,
# but a malformed quote can produce one enormous field. Raise rather than
# truncate so a parse problem surfaces as an error.
csv.field_size_limit(10 * 1024 * 1024)


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# LOAD
# =============================================================================

def load_candidates(path: Path) -> list[dict[str, str]]:
    """Read ahs_candidates.csv, validating the schema at the boundary."""
    if not path.exists():
        die(f"candidates file not found: {path.resolve()}. This script runs on "
            f"WORK, where the AHS Stage 3 output lives. Pass --ahs-dir if it "
            f"lives elsewhere; this script never guesses alternative paths.")
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            die(f"{path} has no header row.")
        missing = [c for c in REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            die(f"{path} missing required column(s) {missing}; "
                f"have {list(reader.fieldnames)}")
        rows = list(reader)
    if not rows:
        die(f"{path} has zero data rows.")
    return rows


def load_expected(path: Path) -> int:
    """Read the expected unique-question count from ahs_candidate_summary.json."""
    if not path.exists():
        die(f"summary file not found: {path.resolve()}. The unique-question "
            f"count is checked against the rollup's own summary; run "
            f"src/core/stage3_ahs_rollup.py first.")
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"{path} is not valid JSON: {e}")
    block = summary.get(EXPECTED_PARENT)
    if isinstance(block, dict) and EXPECTED_KEY in block:
        raw = block[EXPECTED_KEY]
    elif EXPECTED_KEY in summary:
        raw = summary[EXPECTED_KEY]
    else:
        die(f"{path} has no {EXPECTED_PARENT}.{EXPECTED_KEY} (and none at the "
            f"top level); cannot verify the unique-question count. Top-level "
            f"keys present: {sorted(summary)}")
    if not isinstance(raw, int) or isinstance(raw, bool):
        die(f"{EXPECTED_PARENT}.{EXPECTED_KEY} in {path} is {raw!r}, not an "
            f"integer.")
    return raw


# =============================================================================
# BEST TIER PER UNIQUE QUESTION TEXT
# =============================================================================

def best_tier_by_text(rows: list[dict[str, str]]) -> dict[str, dict[str, object]]:
    """Group candidate pairs by unique question text; best tier F1 else F2.

    Text is compared after stripping surrounding whitespace only. No other
    normalization: case and punctuation are meaningful in question wording, and
    the project dedup rule elsewhere is an exact full-text match.
    """
    groups: dict[str, dict[str, object]] = {}
    bad_feas: dict[str, int] = defaultdict(int)
    n_blank_text = 0

    for i, row in enumerate(rows, start=2):  # start=2: line 1 is the header
        feas = (row.get("final_feasibility") or "").strip().upper()
        if feas not in CANDIDATE_FEAS:
            bad_feas[feas or "EMPTY"] += 1
            continue

        text = (row.get("survey_text") or "").strip()
        if not text:
            n_blank_text += 1
            print(f"  line {i}: pair_id "
                  f"{row.get('pair_id', '?')!r} has empty survey_text",
                  file=sys.stderr)
            continue

        g = groups.setdefault(
            text, {"tiers": set(), "q_ids": set(), "pair_ids": set()})
        g["tiers"].add(feas)                                # type: ignore[union-attr]
        g["q_ids"].add((row.get("survey_q_id") or "").strip())  # type: ignore[union-attr]
        g["pair_ids"].add((row.get("pair_id") or "").strip())   # type: ignore[union-attr]

    if bad_feas:
        print("FATAL: ahs_candidates.csv should hold F1/F2 candidate pairs "
              "only. Unexpected final_feasibility values:", file=sys.stderr)
        for value, n in sorted(bad_feas.items()):
            print(f"    {value!r}: {n}", file=sys.stderr)
        die(f"{sum(bad_feas.values())} row(s) are not F1 or F2. Refusing to "
            f"drop rows or assign a best tier from an unknown tier set.")
    if n_blank_text:
        die(f"{n_blank_text} candidate row(s) have empty survey_text; the "
            f"grouping unit is the question text, so a blank text cannot be "
            f"grouped. Fix the upstream rollup output.")

    for text, g in groups.items():
        g["best_tier"] = "F1" if "F1" in g["tiers"] else "F2"  # type: ignore[operator]
    return groups


def check_unique_count(groups: dict[str, dict[str, object]], expected: int,
                       summary_path: Path) -> None:
    """Hard-fail if the unique-text count disagrees with the rollup summary."""
    n_unique = len(groups)
    if n_unique == expected:
        return

    n_ids = len({q for g in groups.values()
                 for q in g["q_ids"]})  # type: ignore[union-attr]
    print(f"FATAL: unique question TEXT count is {n_unique}, but "
          f"{EXPECTED_PARENT}.{EXPECTED_KEY} in {summary_path} is {expected}.",
          file=sys.stderr)
    print(f"  unique survey_q_id values in the same candidate set: {n_ids}",
          file=sys.stderr)
    print(f"  The rollup collapsed on survey_q_id; this script collapses on "
          f"survey_text. A gap means at least one question text carries more "
          f"than one id, so {expected} is an id count, not a text count.",
          file=sys.stderr)
    multi = {t: sorted(g["q_ids"]) for t, g in groups.items()  # type: ignore[arg-type]
             if len(g["q_ids"]) > 1}  # type: ignore[arg-type]
    if multi:
        print(f"  {len(multi)} text(s) map to more than one survey_q_id:",
              file=sys.stderr)
        for text, ids in list(multi.items())[:10]:
            preview = text if len(text) <= 100 else text[:100] + "..."
            print(f"    {ids} -> {preview!r}", file=sys.stderr)
    else:
        print("  No text maps to multiple ids, so the gap is not text "
              "collision. The candidates file and the summary are likely from "
              "different runs.", file=sys.stderr)
    die(f"unique-question count mismatch: {n_unique} (text) != {expected} "
        f"(summary). Refusing to report a split against an unverified "
        f"denominator.")


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="AHS best-tier split per unique question text (F1 else F2).")
    ap.add_argument("--ahs-dir", default=str(DEFAULT_AHS_DIR),
                    help=f"directory holding {CANDIDATES_NAME} and "
                         f"{SUMMARY_NAME} (default: {DEFAULT_AHS_DIR})")
    args = ap.parse_args()

    ahs_dir = Path(args.ahs_dir)
    candidates_path = ahs_dir / CANDIDATES_NAME
    summary_path = ahs_dir / SUMMARY_NAME

    rows = load_candidates(candidates_path)
    expected = load_expected(summary_path)
    groups = best_tier_by_text(rows)
    check_unique_count(groups, expected, summary_path)

    n_unique = len(groups)
    best_f1 = sum(1 for g in groups.values() if g["best_tier"] == "F1")
    best_f2 = sum(1 for g in groups.values() if g["best_tier"] == "F2")

    # The two buckets must partition the set: best_tier is assigned from a
    # non-empty tier set drawn from {F1, F2}, so a gap here is a logic error.
    if best_f1 + best_f2 != n_unique:
        die(f"best-tier buckets do not partition the question set: "
            f"F1({best_f1}) + F2({best_f2}) != unique({n_unique}).")

    print(f"n_unique_questions: {n_unique}")
    print(f"best_tier_f1: {best_f1}")
    print(f"best_tier_f2: {best_f2}")
    print(json.dumps({
        "script": "v2/src/report/ahs_best_tier_split.py",
        "input": str(candidates_path),
        "grouping_unit": "unique survey_text (whitespace-stripped)",
        "best_tier_rule": "F1 if any candidate pair is F1, else F2",
        "n_candidate_pairs": len(rows),
        "n_unique_questions": n_unique,
        "best_tier_f1": best_f1,
        "best_tier_f2": best_f2,
        "expected_unique_from_summary": expected,
        "unique_count_check": "PASS",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
