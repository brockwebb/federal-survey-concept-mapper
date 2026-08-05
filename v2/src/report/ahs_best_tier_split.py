#!/usr/bin/env python3
"""RETIRED 2026-06-11. The AHS best-tier split now comes from the rollup.

This script existed to fill the two `pending` best-tier cells in
`v2/report/three_survey_harmonization_summary.qmd` by collapsing
`ahs_candidates.csv` onto unique question text. Its denominator assert did its
job on the first WORK run and failed: 89 unique question texts against the 92
`survey_q_id` values the rollup had reported. Three AHS question texts carry two
ids each (5583/5597, 5584/5598, 5696/5698), the same id-proliferation inflation
certified and corrected for v1 CPS and FoodAPS in 2026-02.

That made the split a symptom of a larger defect: every AHS question-level
number the rollup published was an id count. Fixing the unit inside the rollup
also produces the best-tier split, so maintaining a second script that
re-derives the same collapse from a downstream CSV would give two code paths
that can disagree. The rollup is now the single source.

Read `best_tier_f1` and `best_tier_f2` from `question_level` in
`output/stage3/results/ahs/ahs_candidate_summary.json`, produced by:

    python src/core/stage3_ahs_rollup.py

Kept as a stub rather than deleted so an operator running the old command by
habit gets this explanation instead of a bare "No such file" from the shell.
See `cc_tasks/2026-06-11_ahs_rollup_text_unit_fix.md`.
"""
from __future__ import annotations

import sys

MESSAGE = __doc__


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
