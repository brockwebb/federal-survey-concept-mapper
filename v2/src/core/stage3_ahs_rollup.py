#!/usr/bin/env python3
"""AHS Stage 3 harmonization candidate rollup (net-new, NO v1 baseline).

AHS is a HUD add-on to the ACS family and is net-new in v2: it has no v1
classification to compare against. So unlike CPS and FoodAPS it gets NO
v1-vs-v2 reproducibility comparison. It is reported on its own terms: a
filter-and-summarize over the final barrier classification CSV that surfaces
where the harmonization candidates are.

WHAT THIS IS NOT
----------------
This is a descriptive rollup of already-classified data. No model calls, no
harness, pure pandas. It does NOT validate the F3 floor (AHS has no v1 baseline
to cross-check discards against, unlike CPS/FoodAPS whose F3 discards reproduced
at ~97% vs v1). The ~130 non-F3 candidates are a v2-ONLY signal with
single-generation provenance, not the dual-generation intersection that backs
the CPS/FoodAPS gold set. The output MD states this caveat plainly; this script
exists to produce numbers, not to claim they are validated.

CANDIDATE DEFINITION (identical to stage3_v1_v2_signal_stratified.py)
--------------------------------------------------------------------
A pair is a CANDIDATE if final_feasibility is F1 or F2; a DISCARD if F3. NHB
pairs (the rater prompt's no-barrier code) are always F1, so they fall under the
F1 candidate rule automatically. The script buckets purely by final_feasibility
and ASSERTS that candidate + discard == total: any other value (NHB-as-feas,
null from a failed row) is a finding reported loudly, never silently dropped.

UNIT DISCIPLINE (the 2026-06-03 revision)
-----------------------------------------
The tier counts (F1/F2/F3) are counts of PAIRS, an intermediate unit: one AHS
question pairs against several ACS questions sharing a subtopic, so the pair
total is pair-instances, not questions. The deliverable statement must be in
QUESTIONS: of the N AHS questions that entered harmonization pairing, X have at
least one candidate (F1/F2) match into ACS. The question-level denominators come
from the pair builder's own pair_summary.json (Definition B: AHS column non-empty
in PublicSurveyQuestionsMap), never recomputed here, so numerator and denominator
describe the same population. The numerator collapses the F1/F2 pair set onto
survey_q_id (the AHS-side question id). Pair-level counts are kept and reported,
but labeled explicitly as pairs so the two units are never conflated again.

Run from v2/ (the AHS data lives on WORK only; authored on DEV, run on WORK):
    python src/core/stage3_ahs_rollup.py
    python src/core/stage3_ahs_rollup.py --ahs-dir output/stage3/results/ahs \
        --pairs-dir output/stage3/candidate_pairs
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd


# =============================================================================
# CONSTANTS / PATHS (defaults assume cwd == v2/)
# =============================================================================

DEFAULT_AHS_DIR = Path("output/stage3/results/ahs")
INPUT_NAME = "final_barrier_classifications.csv"

# Pair builder outputs (mirrors config/stage3.yaml output.output_dir +
# output.pairs_subdir + output.pair_summary_json). The question-level
# denominators are read from these, NOT recomputed: pair_summary.json carries
# the exact Definition-B population the pairing used, and the pairs file carries
# the entered-pairing question set keyed on survey_q_id.
DEFAULT_PAIRS_DIR = Path("output/stage3/candidate_pairs")
PAIR_SUMMARY_NAME = "pair_summary.json"
PAIRS_AHS_NAME = "pairs_ahs.csv"
AHS_SURVEY_KEY = "ahs"   # key under pair_summary.json -> surveys

CANDIDATE_FEAS = {"F1", "F2"}   # F3 = discard
DISCARD_FEAS = {"F3"}

# The gemini-2.5-pro recovery pair; must survive as a real (non-null) row.
CHECK_PAIR_ID = "AHS_00783"

# Cap the F2 listing in the narrative MD (the CSV always carries the full set).
F2_LIST_CAP = 25

# Full schema produced by merge_final() in stage3_barrier_classify.py. Every one
# of these must be present; a missing column means the input is not the file we
# think it is, so we fail rather than guess.
REQUIRED_COLUMNS = [
    "pair_id", "source_survey", "survey_q_id", "acs_q_id", "shared_topic",
    "shared_subtopic", "survey_text", "acs_text", "final_classification",
    "final_primary_barrier", "final_feasibility", "final_confidence",
    "decision_method", "rater_a_primary_barrier", "rater_a_feasibility",
    "rater_a_confidence", "rater_b_primary_barrier", "rater_b_feasibility",
    "rater_b_confidence", "rater_a_status", "rater_b_status",
    "arbitrator_status",
]

# Columns carried into the candidate CSV / strongest-leads listing.
# survey_q_id and shared_topic are carried so the question-level rollup
# (collapse on survey_q_id, reach by topic/subtopic) is auditable straight
# from ahs_candidates.csv, not only from the in-memory frame.
CANDIDATE_COLS = [
    "pair_id", "survey_q_id", "final_feasibility", "shared_topic",
    "shared_subtopic", "survey_text", "acs_text", "final_primary_barrier",
    "final_confidence", "decision_method",
]


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# HELPERS
# =============================================================================

def _norm_feas(v: Any) -> str:
    """Upper-cased, stripped feasibility token; '' for null/NaN."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip().upper()


def _counts(series: pd.Series) -> dict[str, int]:
    """value_counts as an ordered plain dict, NaN rendered as the string
    'NULL' so a missing classification is visible, not dropped."""
    vc = series.where(series.notna(), other="NULL").astype(str).value_counts()
    return {str(k): int(v) for k, v in vc.items()}


def _num(v: Any) -> float | None:
    try:
        f = float(v)
        return f if f == f else None  # drop NaN
    except (TypeError, ValueError):
        return None


# =============================================================================
# LOAD + BUCKET
# =============================================================================

def load_ahs(input_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        die(f"AHS input not found: {input_path.resolve()}. This rollup runs on "
            f"WORK, where the AHS Stage 3 output lives.")
    # utf-8 so the ACS-side text (known cp1252 mojibake) displays as authored;
    # any surviving mojibake is cosmetic and noted in the MD, not blocking.
    df = pd.read_csv(input_path, encoding="utf-8")
    if df.empty:
        die(f"AHS input {input_path} has zero rows.")
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        die(f"AHS input missing required column(s) {missing}; "
            f"have {list(df.columns)}")
    return df


def bucket(df: pd.DataFrame) -> dict[str, Any]:
    """Bucket by final_feasibility and assert candidate + discard == total."""
    feas = df["final_feasibility"].map(_norm_feas)
    cand_mask = feas.isin(CANDIDATE_FEAS)
    disc_mask = feas.isin(DISCARD_FEAS)

    n_total = len(df)
    n_cand = int(cand_mask.sum())
    n_disc = int(disc_mask.sum())

    if n_cand + n_disc != n_total:
        # An unexpected feasibility value (NHB-as-feasibility, a null from a
        # failed row, a typo) is a finding, not noise. Show it and stop.
        vc = feas.where(feas != "", other="NULL").value_counts()
        print("FATAL: candidate + discard != total. Unexpected "
              "final_feasibility values present:", file=sys.stderr)
        for k, v in vc.items():
            print(f"    {k!r}: {v}", file=sys.stderr)
        die(f"buckets do not sum: candidate({n_cand}) + discard({n_disc}) "
            f"!= total({n_total}). Refusing to drop rows.")

    f1 = int((feas == "F1").sum())
    f2 = int((feas == "F2").sum())
    f3 = int((feas == "F3").sum())
    return {
        "cand_mask": cand_mask, "disc_mask": disc_mask, "feas": feas,
        "n_total": n_total, "n_cand": n_cand, "n_disc": n_disc,
        "f1": f1, "f2": f2, "f3": f3,
    }


# =============================================================================
# SUMMARY (the source-of-truth numbers)
# =============================================================================

def build_summary(df: pd.DataFrame, b: dict[str, Any],
                  input_path: Path) -> dict[str, Any]:
    cand = df[b["cand_mask"]].copy()
    n_total = b["n_total"]

    # NHB visibility: count rows whose classification or barrier is NHB. The
    # WORK one-liner showed no NHB rows for AHS, but we measure rather than
    # assume.
    cls_upper = df["final_classification"].astype(str).str.upper()
    bar_upper = df["final_primary_barrier"].astype(str).str.upper()
    nhb_count = int((cls_upper.eq("NHB") | bar_upper.str.startswith("NHB")).sum())

    # AHS_00783 presence + non-null check.
    hit = df[df["pair_id"] == CHECK_PAIR_ID]
    if hit.empty:
        check = {"present": False, "row": None, "feasibility_non_null": False}
    else:
        row = hit.iloc[0]
        check = {
            "present": True,
            "feasibility_non_null": _norm_feas(row["final_feasibility"]) != "",
            "row": {
                "pair_id": str(row["pair_id"]),
                "final_classification": (None if pd.isna(row["final_classification"])
                                         else str(row["final_classification"])),
                "final_primary_barrier": (None if pd.isna(row["final_primary_barrier"])
                                          else str(row["final_primary_barrier"])),
                "final_feasibility": (None if pd.isna(row["final_feasibility"])
                                      else str(row["final_feasibility"])),
                "final_confidence": _num(row["final_confidence"]),
                "decision_method": (None if pd.isna(row["decision_method"])
                                    else str(row["decision_method"])),
                "shared_subtopic": (None if pd.isna(row["shared_subtopic"])
                                    else str(row["shared_subtopic"])),
            },
        }

    def pct(n: int) -> float:
        return round(n / n_total * 100, 2) if n_total else 0.0

    return {
        "input_path": str(input_path),
        "encoding": "utf-8",
        # UNIT: every count in this block is over PAIRS, an intermediate unit.
        # The deliverable question-level numbers live under `question_level`,
        # added in main(). These keys are named so they cannot be misread as
        # question counts.
        "unit_note": "feasibility_tiers and *_pairs counts are PAIR counts, not "
                     "questions; see question_level for the deliverable unit.",
        "total_pairs": n_total,
        "pairs_total": n_total,
        "candidates_pairs": b["n_cand"],
        "candidate_definition": "final_feasibility in {F1, F2}; discard = F3",
        "feasibility_tiers": {
            "unit": "pairs",
            "F1": b["f1"], "F2": b["f2"], "F3": b["f3"],
            "candidate_count": b["n_cand"], "discard_count": b["n_disc"],
            "candidate_pct": pct(b["n_cand"]), "discard_pct": pct(b["n_disc"]),
        },
        "bucket_sum_ok": (b["n_cand"] + b["n_disc"] == n_total),
        "nhb_count": nhb_count,
        # step 4: barrier composition WITHIN the candidate set (F1/F2 only)
        "candidate_barrier_composition": _counts(cand["final_primary_barrier"]),
        # step 5: classification composition across ALL pairs (DESCRIPTIVE ONLY,
        # not a claim about the F3-attractor)
        "all_classification_composition_descriptive":
            _counts(df["final_classification"]),
        # step 7: decision_method provenance for the candidate set
        "candidate_decision_method": _counts(cand["decision_method"]),
        "check_pair": check,
    }


# =============================================================================
# QUESTION-LEVEL ROLLUP (the deliverable unit) + TOPIC/SUBTOPIC REACH
# =============================================================================

# Keys that MUST exist in pair_summary.json -> surveys.ahs. A missing key means
# the summary was written by a pair builder that predates the diagnostics block,
# so we fail rather than guess a denominator.
PAIR_SUMMARY_AHS_KEYS = [
    "source_questions_in_map", "source_after_master_join", "shared_subtopics",
]


def load_pair_summary_ahs(pairs_dir: Path) -> dict[str, Any]:
    """Read surveys.ahs from pair_summary.json. This is the Definition-B
    population the pairing used; the question-level denominators come from here
    and are never recomputed in this script."""
    path = pairs_dir / PAIR_SUMMARY_NAME
    if not path.exists():
        die(f"pair_summary.json not found: {path.resolve()}. The question-level "
            f"denominators are read from the pair builder's summary; run "
            f"stage3_pair_builder.py first, or pass --pairs-dir.")
    try:
        summary = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        die(f"pair_summary.json is not valid JSON ({path}): {e}")
    surveys = summary.get("surveys")
    if not isinstance(surveys, dict) or AHS_SURVEY_KEY not in surveys:
        die(f"pair_summary.json has no surveys.{AHS_SURVEY_KEY} block: {path}")
    block = surveys[AHS_SURVEY_KEY]
    missing = [k for k in PAIR_SUMMARY_AHS_KEYS if k not in block]
    if missing:
        die(f"pair_summary.json surveys.{AHS_SURVEY_KEY} missing key(s) "
            f"{missing}; have {list(block.keys())}")
    return block


def load_pairs_ahs(pairs_dir: Path) -> pd.DataFrame:
    """Read pairs_ahs.csv -- the entered-pairing question set. Used only for the
    set of survey_q_ids that produced >=1 pair and their topic/subtopic; the
    DENOMINATOR counts come from pair_summary.json, not from this file's row
    count (the pairs file structurally excludes any AHS question that produced
    zero pairs)."""
    path = pairs_dir / PAIRS_AHS_NAME
    if not path.exists():
        die(f"pairs_ahs.csv not found: {path.resolve()}. Pass --pairs-dir if it "
            f"lives elsewhere; this script never guesses alternative paths.")
    df = pd.read_csv(path, encoding="utf-8")
    needed = ["survey_q_id", "shared_topic", "shared_subtopic"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        die(f"pairs_ahs.csv missing column(s) {missing}; have {list(df.columns)}")
    df["survey_q_id"] = df["survey_q_id"].astype(int)
    return df


def _assert_single_subtopic(df: pd.DataFrame, label: str) -> None:
    """Each AHS question carries a single final_subtopic (and therefore a single
    topic), so a survey_q_id must map to exactly one (shared_topic,
    shared_subtopic). If that invariant breaks, the reach numerators would
    double-count and the per-cell sums would no longer reconcile to the
    question total, so we fail loudly with the offenders rather than silently
    over-count."""
    g = df.groupby("survey_q_id")
    multi_sub = g["shared_subtopic"].nunique()
    multi_top = g["shared_topic"].nunique()
    bad = sorted(set(multi_sub[multi_sub > 1].index)
                 | set(multi_top[multi_top > 1].index))
    if bad:
        die(f"{label}: {len(bad)} survey_q_id(s) span >1 topic/subtopic "
            f"(e.g. {bad[:10]}); the single-subtopic-per-question invariant is "
            f"broken and the reach partition would over-count.")


def _reach_by(group_col: str, pairs_ahs: pd.DataFrame,
              cand: pd.DataFrame, sub_to_topic: dict[str, str] | None
              ) -> list[dict[str, Any]]:
    """Three-column reach cut on the UNIQUE-QUESTION unit:
        entered        = distinct survey_q_id in pairs_ahs within the cell
        with_candidate = distinct survey_q_id in the F1/F2 set within the cell
        reach_pct      = with_candidate / entered * 100
    Denominator from pairs_ahs, numerator from the candidate set: same
    population both sides (candidates are a subset of entered-pairing pairs).
    Sorted by `entered` descending."""
    den = pairs_ahs.groupby(group_col)["survey_q_id"].nunique()
    num = cand.groupby(group_col)["survey_q_id"].nunique()
    rows: list[dict[str, Any]] = []
    for key, a in den.items():
        a = int(a)
        b = int(num.get(key, 0))
        row: dict[str, Any] = {group_col: str(key)}
        if sub_to_topic is not None:
            row["shared_topic"] = sub_to_topic.get(str(key), "")
        row["entered"] = a
        row["with_candidate"] = b
        row["reach_pct"] = round(b / a * 100, 2) if a else 0.0
        rows.append(row)
    rows.sort(key=lambda r: r["entered"], reverse=True)
    return rows


def build_question_level(df: pd.DataFrame, b: dict[str, Any],
                         pairs_ahs: pd.DataFrame,
                         ahs_block: dict[str, Any]) -> dict[str, Any]:
    """Collapse the F1/F2 pair set to unique AHS questions and reconcile against
    the Definition-B population from pair_summary.json. All denominators come
    from pair_summary.json; the numerator collapses the candidate pairs onto
    survey_q_id. The two no-candidate buckets are reported separately and the
    three-way partition of the entered-pairing population is asserted."""
    cand = df[b["cand_mask"]].copy()
    cand["survey_q_id"] = cand["survey_q_id"].astype(int)

    # Denominators -- read straight from the pair builder's summary.
    in_map = int(ahs_block["source_questions_in_map"])
    entered = int(ahs_block["source_after_master_join"])
    shared_subtopics = int(ahs_block["shared_subtopics"])

    # Entered-pairing questions that actually produced >=1 pair (shared a
    # subtopic with ACS). The rest of `entered` shared no subtopic -> 0 pairs.
    producing_ids = set(pairs_ahs["survey_q_id"].tolist())
    producing = len(producing_ids)

    # Numerator: unique AHS questions with >=1 F1/F2 candidate pair.
    cand_ids = set(cand["survey_q_id"].tolist())
    with_candidate = len(cand_ids)

    # Integrity: candidates come from classified pairs, so every candidate
    # survey_q_id must be among the questions that produced pairs.
    stray = sorted(cand_ids - producing_ids)
    if stray:
        die(f"{len(stray)} candidate survey_q_id(s) are absent from pairs_ahs.csv "
            f"(e.g. {stray[:10]}); candidate and pair populations disagree.")
    if producing > entered:
        die(f"questions producing pairs ({producing}) exceeds entered-pairing "
            f"population ({entered}) from pair_summary.json; populations "
            f"disagree -- pairs_dir and ahs_dir may be from different runs.")
    if with_candidate > producing:
        die(f"unique questions with candidate ({with_candidate}) exceeds "
            f"questions producing pairs ({producing}); impossible.")
    # Verification check 3: the question count cannot exceed the pair count.
    if with_candidate > b["n_cand"]:
        die(f"unique questions with candidate ({with_candidate}) exceeds the "
            f"candidate PAIR count ({b['n_cand']}); a question collapses to one, "
            f"so this must be <=.")

    # Two distinct no-candidate buckets (do not lump):
    #   bucket 1 -- entered pairing AND produced pairs, but none are F1/F2.
    #   bucket 2 -- entered pairing but produced zero pairs (no shared subtopic
    #               with ACS): the genuinely AHS-unique territory.
    no_candidate_entered_all_f3 = producing - with_candidate
    no_pair_no_shared_subtopic = entered - producing
    dropped_at_master_join = in_map - entered

    # Partition assertions -- fail loud if the population does not reconcile.
    part = with_candidate + no_candidate_entered_all_f3 + no_pair_no_shared_subtopic
    if part != entered:
        die(f"question buckets do not partition entered-pairing population: "
            f"with_candidate({with_candidate}) + all_f3({no_candidate_entered_all_f3}) "
            f"+ no_pair({no_pair_no_shared_subtopic}) = {part} != {entered}.")
    if entered + dropped_at_master_join != in_map:
        die(f"in-map accounting does not reconcile: entered({entered}) + "
            f"dropped_at_master_join({dropped_at_master_join}) != in_map({in_map}).")

    # Reach cuts on the unique-question unit. Both sides obey the
    # one-subtopic-per-question invariant, so each question lands in exactly one
    # topic row and one subtopic row, and the numerators sum to with_candidate.
    _assert_single_subtopic(pairs_ahs, "pairs_ahs.csv")
    _assert_single_subtopic(cand, "candidate set")
    sub_to_topic = (
        pairs_ahs.drop_duplicates("shared_subtopic")
        .set_index(pairs_ahs.drop_duplicates("shared_subtopic")["shared_subtopic"]
                   .astype(str))["shared_topic"].astype(str).to_dict()
    )
    topic_reach = _reach_by("shared_topic", pairs_ahs, cand, None)
    subtopic_reach = _reach_by("shared_subtopic", pairs_ahs, cand, sub_to_topic)

    # Verification check 4: numerators sum to the unique-question total.
    tsum = sum(r["with_candidate"] for r in topic_reach)
    ssum = sum(r["with_candidate"] for r in subtopic_reach)
    if tsum != with_candidate:
        die(f"topic_reach numerators sum to {tsum}, expected {with_candidate}.")
    if ssum != with_candidate:
        die(f"subtopic_reach numerators sum to {ssum}, expected {with_candidate}.")
    # Denominators sum to the producing-pairs total (each producing question in
    # exactly one topic/subtopic).
    if sum(r["entered"] for r in topic_reach) != producing:
        die("topic_reach denominators do not sum to questions-producing-pairs.")
    if sum(r["entered"] for r in subtopic_reach) != producing:
        die("subtopic_reach denominators do not sum to questions-producing-pairs.")

    reach_pct = round(with_candidate / entered * 100, 2) if entered else 0.0
    return {
        "population_definition":
            "Definition B: AHS column non-empty in PublicSurveyQuestionsMap, "
            "sourced from pair_summary.json (the population the pairing used).",
        "denominator_source": str(pairs_dir_for_msg()),
        "ahs_questions_in_map": in_map,
        "ahs_questions_entered_pairing": entered,
        "dropped_at_master_join": dropped_at_master_join,
        "ahs_questions_producing_pairs": producing,
        "unique_ahs_questions_with_candidate": with_candidate,
        "reach_pct": reach_pct,
        "no_candidate_entered_all_f3": no_candidate_entered_all_f3,
        "no_pair_no_shared_subtopic": no_pair_no_shared_subtopic,
        "shared_subtopics": shared_subtopics,
        "partition_ok": True,
        "subtopic_reach_convention":
            "Each AHS question carries a single final_subtopic, so it is counted "
            "in exactly one topic row and one subtopic row; numerators sum to "
            "unique_ahs_questions_with_candidate.",
        "topic_reach": topic_reach,
        "subtopic_reach": subtopic_reach,
    }


# Set by main() so build_question_level can record which pairs dir the
# denominators came from without threading the path through every call.
_PAIRS_DIR_FOR_MSG: Path | None = None


def pairs_dir_for_msg() -> Path:
    return _PAIRS_DIR_FOR_MSG if _PAIRS_DIR_FOR_MSG is not None else DEFAULT_PAIRS_DIR


# =============================================================================
# CANDIDATE CSV + STRONGEST LEADS
# =============================================================================

def candidate_frame(df: pd.DataFrame, b: dict[str, Any]) -> pd.DataFrame:
    """All F1/F2 candidates, sorted F1 before F2 then confidence desc."""
    cand = df[b["cand_mask"]].copy()
    cand = cand[[c for c in CANDIDATE_COLS if c in cand.columns]].copy()
    cand["_feas"] = cand["final_feasibility"].map(_norm_feas)
    cand["_tier_rank"] = cand["_feas"].map({"F1": 0, "F2": 1}).fillna(9)
    cand["_conf"] = pd.to_numeric(cand["final_confidence"], errors="coerce")
    cand = cand.sort_values(
        by=["_tier_rank", "_conf"], ascending=[True, False],
        na_position="last").drop(columns=["_feas", "_tier_rank", "_conf"])
    return cand.reset_index(drop=True)


# =============================================================================
# REPORT (reads numbers from the summary JSON; hardcodes none)
# =============================================================================

def _row_lines(rows: pd.DataFrame) -> list[str]:
    """Markdown table for a slice of the candidate frame."""
    L = ["| pair_id | subtopic | barrier | conf | method | survey text | ACS text |",
         "|---|---|---|---|---|---|---|"]
    for _, r in rows.iterrows():
        conf = _num(r.get("final_confidence"))
        conf_s = f"{conf:.2f}" if conf is not None else "n/a"
        def cell(v: Any) -> str:
            s = "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
            return s.replace("|", "/").replace("\n", " ").strip()
        L.append(
            f"| {cell(r.get('pair_id'))} | {cell(r.get('shared_subtopic'))} "
            f"| {cell(r.get('final_primary_barrier'))} | {conf_s} "
            f"| {cell(r.get('decision_method'))} | {cell(r.get('survey_text'))} "
            f"| {cell(r.get('acs_text'))} |")
    return L


def write_md(summary: dict[str, Any], cand: pd.DataFrame, out_md: Path,
             f2_cap: int) -> None:
    s = summary
    tiers = s["feasibility_tiers"]
    chk = s["check_pair"]
    q = s["question_level"]
    L: list[str] = []

    L.append("# AHS Harmonization Candidate Rollup")
    L.append("")
    L.append(f"Source: `{s['input_path']}` (read {s['encoding']}); the numbers "
             f"in this document are read from `ahs_candidate_summary.json` and "
             f"none are hardcoded here.")
    L.append("")

    # (0) HEADLINE -- question-level, the deliverable unit, stated first.
    L.append("## Harmonization reach")
    L.append("")
    L.append(f"Of the {q['ahs_questions_entered_pairing']} AHS questions that "
             f"entered harmonization pairing, "
             f"*{q['unique_ahs_questions_with_candidate']}* have at least one "
             f"candidate match into ACS, a feasibility F1 or F2 pair, which is a "
             f"reach of *{q['reach_pct']} percent*. The population that entered "
             f"pairing is the AHS questions present in the survey-question map "
             f"that survived the master-classification join, read from the pair "
             f"builder's `pair_summary.json` so the numerator and denominator "
             f"describe the same Definition-B population.")
    L.append("")
    L.append(f"That reach is the question-level result and is the unit to cite, "
             f"while the pair-level view is secondary, with "
             f"{s['candidates_pairs']} candidate pairs out of {s['pairs_total']} "
             f"total pairs ({tiers['candidate_pct']} percent of pairs), an "
             f"intermediate unit because one AHS question pairs against several "
             f"ACS questions, so the pair percentage and the question percentage "
             f"measure different things and only the question figure is a "
             f"deliverable statement.")
    L.append("")

    # (0b) The two no-candidate buckets, kept separate.
    L.append("## Questions with no candidate, split by reason")
    L.append("")
    L.append("An AHS question with no candidate falls into one of two distinct "
             "buckets, and lumping them would hide the finding.")
    L.append("")
    L.append("| bucket | questions | meaning |")
    L.append("|---|---|---|")
    L.append(f"| entered pairing, all pairs F3 | {q['no_candidate_entered_all_f3']} "
             f"| ACS covers this territory, but in a form judged not harmonizable |")
    L.append(f"| no pair, no shared subtopic | {q['no_pair_no_shared_subtopic']} "
             f"| genuinely AHS-specific: no ACS counterpart territory at all |")
    L.append(f"| has a candidate | {q['unique_ahs_questions_with_candidate']} "
             f"| at least one F1 or F2 match into ACS |")
    L.append(f"| entered pairing (total) | {q['ahs_questions_entered_pairing']} "
             f"| the three rows above partition this population |")
    L.append("")
    L.append(f"The no-pair bucket is the actionable finding, since those "
             f"{q['no_pair_no_shared_subtopic']} questions sit in subtopics ACS "
             f"does not enter and are therefore AHS-unique content rather than a "
             f"harmonization failure, while a further "
             f"{q['dropped_at_master_join']} AHS questions present in the map were "
             f"dropped before pairing at the master-classification join "
             f"(Unresolvable or empty text), leaving "
             f"{q['ahs_questions_entered_pairing']} of "
             f"{q['ahs_questions_in_map']} in-map questions in the analysis.")
    L.append("")

    # (0c) Reach by topic and subtopic, on the unique-question unit.
    L.append("## Reach by topic")
    L.append("")
    L.append("Each row counts unique AHS questions, not pairs. The "
             "denominator is questions that entered pairing in that topic and "
             "produced at least one pair; the numerator is those with at least "
             "one candidate. " + q["subtopic_reach_convention"])
    L.append("")
    L.append("| topic | entered | with candidate | reach % |")
    L.append("|---|---|---|---|")
    for r in q["topic_reach"]:
        L.append(f"| {r['shared_topic']} | {r['entered']} "
                 f"| {r['with_candidate']} | {r['reach_pct']}% |")
    L.append("")
    L.append("## Reach by subtopic")
    L.append("")
    L.append("The actionable view: which AHS subtopics map into ACS and which "
             "are AHS-specific. Unique questions, not pairs.")
    L.append("")
    L.append("| subtopic | topic | entered | with candidate | reach % |")
    L.append("|---|---|---|---|---|")
    for r in q["subtopic_reach"]:
        L.append(f"| {r['shared_subtopic']} | {r.get('shared_topic', '')} "
                 f"| {r['entered']} | {r['with_candidate']} "
                 f"| {r['reach_pct']}% |")
    L.append("")

    # (a) what AHS is
    L.append("## What AHS is")
    L.append("")
    L.append("The American Housing Survey is a HUD add-on to the American "
             "Community Survey family that, in this analysis, is net-new: it "
             "was classified for the first time in the v2 confirmation run and "
             "has no v1 baseline, so it receives no v1-versus-v2 reproducibility "
             "comparison and is reported on its own terms.")
    L.append("")

    # (b) tier table
    L.append("## Feasibility tiers (pair counts)")
    L.append("")
    L.append("Every count in this table is a count of pairs, the intermediate "
             "unit, not of questions. The question-level reach is in the "
             "headline above.")
    L.append("")
    L.append("| tier | pairs | share of pairs |")
    L.append("|---|---|---|")
    L.append(f"| F1 direct recode | {tiers['F1']} | "
             f"{round(tiers['F1'] / s['total_pairs'] * 100, 2)}% |")
    L.append(f"| F2 statistical adjustment | {tiers['F2']} | "
             f"{round(tiers['F2'] / s['total_pairs'] * 100, 2)}% |")
    L.append(f"| F3 incompatible (discard) | {tiers['F3']} | "
             f"{tiers['discard_pct']}% |")
    L.append(f"| candidate (F1+F2) | {tiers['candidate_count']} | "
             f"{tiers['candidate_pct']}% |")
    L.append(f"| total | {s['total_pairs']} | 100% |")
    L.append("")

    # (c) the caveat, stated plainly and up front
    L.append("## Caveat: the candidates are a v2-only, unvalidated signal")
    L.append("")
    L.append(f"{tiers['discard_pct']} percent of AHS pairs are F3, the "
             f"incompatible tier, which leaves the {tiers['candidate_count']} "
             f"non-F3 candidates as the entire AHS harmonization story, sitting "
             f"on that discard floor.")
    L.append("")
    L.append("That floor cannot be validated the way the CPS and FoodAPS "
             "floors were. The CPS and FoodAPS F3 discards were cross-checked "
             "against the v1 run and reproduced at roughly 97 percent, which is "
             "independent evidence that those discards are correct. AHS has no "
             "v1 baseline, so there is no independent check on whether its F3 "
             "pairs are correctly discarded or are being swallowed by the "
             "documented v2 F3-attractor. For AHS that question is open and "
             "cannot be answered from reproducibility, and it is a limitation "
             "of this rollup rather than a settled result.")
    L.append("")
    L.append("The candidates carry single-generation provenance: they are the "
             "strongest available AHS harmonization leads, but they were "
             "produced by one model generation and lack the dual-generation "
             "intersection that backs the CPS and FoodAPS gold set, so they are "
             "reported here as the v2 candidate set and not as a validated "
             "result.")
    L.append("")

    # (d) where the candidates cluster
    L.append("## Where the candidates cluster")
    L.append("")
    L.append("Barrier composition within the candidate set (F1 and F2 only), "
             "by final primary barrier code:")
    L.append("")
    L.append("| barrier | count |")
    L.append("|---|---|")
    for code, n in s["candidate_barrier_composition"].items():
        L.append(f"| {code} | {n} |")
    L.append("")

    # (e) strongest leads
    cand["_feas"] = cand["final_feasibility"].map(_norm_feas)
    f1 = cand[cand["_feas"] == "F1"].drop(columns=["_feas"])
    f2 = cand[cand["_feas"] == "F2"].drop(columns=["_feas"])
    L.append("## Strongest leads")
    L.append("")
    L.append(f"F1 pairs are the cleanest harmonization path, a direct recode, "
             f"and all {len(f1)} F1 candidates follow.")
    L.append("")
    L.extend(_row_lines(f1))
    L.append("")
    if len(f2):
        if len(f2) > f2_cap:
            L.append(f"F2 pairs require a statistical adjustment, and the top "
                     f"{f2_cap} of {len(f2)} by confidence follow; the "
                     f"full set is in `ahs_candidates.csv`.")
            L.append("")
            L.extend(_row_lines(f2.head(f2_cap)))
        else:
            L.append(f"F2 pairs require a statistical adjustment, and all "
                     f"{len(f2)} F2 candidates follow.")
            L.append("")
            L.extend(_row_lines(f2))
        L.append("")

    # (f) provenance note
    L.append("## Decision-method provenance")
    L.append("")
    L.append("A candidate that both raters independently called F1 or F2 is "
             "stronger evidence than one that exists only because the "
             "arbitrator broke a tie, so the breakdown for the candidate set "
             "follows as the AHS analogue of the confidence gating that "
             "produces the CPS and FoodAPS gold set.")
    L.append("")
    L.append("| decision_method | candidate count |")
    L.append("|---|---|")
    for method, n in s["candidate_decision_method"].items():
        L.append(f"| {method} | {n} |")
    L.append("")

    # classification composition (descriptive only)
    L.append("## Classification composition across all pairs (descriptive)")
    L.append("")
    L.append("The following counts the bare Level 1 classification across all "
             "AHS pairs, including the F3 floor, as descriptive context for the "
             "composition of the discards, and it is not evidence of the "
             "F3-attractor, which is a separate and prompt-confounded finding "
             "documented in the TEVV prompt-equivalence work.")
    L.append("")
    L.append("| classification | count |")
    L.append("|---|---|")
    for code, n in s["all_classification_composition_descriptive"].items():
        L.append(f"| {code} | {n} |")
    L.append("")

    # recovery pair check
    L.append("## Recovery pair check")
    L.append("")
    if chk["present"] and chk["feasibility_non_null"]:
        row = chk["row"]
        L.append(f"{CHECK_PAIR_ID}, the gemini-2.5-pro recovery pair, is present "
                 f"and landed as a real row with feasibility "
                 f"{row['final_feasibility']}, barrier {row['final_primary_barrier']}, "
                 f"by {row['decision_method']}.")
    elif chk["present"]:
        L.append(f"WARNING: {CHECK_PAIR_ID} is present but its feasibility is "
                 f"null, meaning it landed as a failed row. Investigate before "
                 f"using this rollup.")
    else:
        L.append(f"WARNING: {CHECK_PAIR_ID} is absent from the input. The "
                 f"recovery pair did not make it into the final classifications.")
    L.append("")

    out_md.write_text("\n".join(L), encoding="utf-8")


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="AHS Stage 3 harmonization candidate rollup "
                    "(net-new, no v1 baseline).")
    ap.add_argument("--ahs-dir", default=str(DEFAULT_AHS_DIR),
                    help="directory holding final_barrier_classifications.csv "
                         "and receiving the rollup outputs "
                         f"(default: {DEFAULT_AHS_DIR})")
    ap.add_argument("--pairs-dir", default=str(DEFAULT_PAIRS_DIR),
                    help="directory holding pair_summary.json and pairs_ahs.csv "
                         "(the question-level denominators; mirrors "
                         "stage3.yaml output.output_dir + output.pairs_subdir; "
                         f"default: {DEFAULT_PAIRS_DIR})")
    ap.add_argument("--f2-cap", type=int, default=F2_LIST_CAP,
                    help="cap the F2 listing in the MD (CSV is never capped)")
    args = ap.parse_args()

    global _PAIRS_DIR_FOR_MSG
    ahs_dir = Path(args.ahs_dir)
    pairs_dir = Path(args.pairs_dir)
    _PAIRS_DIR_FOR_MSG = pairs_dir
    input_path = ahs_dir / INPUT_NAME
    out_json = ahs_dir / "ahs_candidate_summary.json"
    out_csv = ahs_dir / "ahs_candidates.csv"
    out_md = ahs_dir / "ahs_rollup.md"

    print("=" * 70)
    print("AHS HARMONIZATION CANDIDATE ROLLUP (net-new, no v1 baseline)")
    print("=" * 70)

    df = load_ahs(input_path)
    b = bucket(df)
    summary = build_summary(df, b, input_path)

    # Question-level rollup: denominators from the pair builder's summary, the
    # numerator collapsed onto survey_q_id. This is the deliverable unit.
    ahs_block = load_pair_summary_ahs(pairs_dir)
    pairs_ahs = load_pairs_ahs(pairs_dir)
    summary["question_level"] = build_question_level(df, b, pairs_ahs, ahs_block)

    # write the source-of-truth JSON first, then read it back so the CSV and MD
    # are generated from the serialized numbers, never from a parallel path.
    ahs_dir.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary = json.loads(out_json.read_text(encoding="utf-8"))

    cand = candidate_frame(df, b)
    cand.to_csv(out_csv, index=False, encoding="utf-8")
    if len(cand) != b["n_cand"]:
        die(f"candidate CSV has {len(cand)} rows but bucket counted "
            f"{b['n_cand']} candidates; sorting dropped rows.")

    write_md(summary, cand, out_md, args.f2_cap)

    tiers = summary["feasibility_tiers"]
    chk = summary["check_pair"]
    q = summary["question_level"]
    print(f"  wrote: {out_json}")
    print(f"  wrote: {out_csv}  ({len(cand)} candidate pairs)")
    print(f"  wrote: {out_md}")
    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    # Question-level statement FIRST -- the deliverable unit.
    print(f"  QUESTIONS: of {q['ahs_questions_entered_pairing']} AHS questions "
          f"that entered pairing, {q['unique_ahs_questions_with_candidate']} have "
          f">=1 candidate (F1/F2) match into ACS ({q['reach_pct']}%).")
    print(f"  no candidate, entered + all F3 (bucket 1): "
          f"{q['no_candidate_entered_all_f3']}")
    print(f"  no pair, no shared subtopic (bucket 2, AHS-unique): "
          f"{q['no_pair_no_shared_subtopic']}")
    print(f"  PAIRS (intermediate unit): {tiers['candidate_count']} candidate "
          f"pairs of {summary['pairs_total']} total ({tiers['candidate_pct']}% "
          f"of pairs)")
    print(f"  F1 / F2 / F3 pairs: {tiers['F1']} / {tiers['F2']} / {tiers['F3']}")
    print(f"  discard (F3) pairs: {tiers['discard_count']} "
          f"({tiers['discard_pct']}%)")
    print(f"  {CHECK_PAIR_ID} present: {chk['present']} "
          f"(feasibility non-null: {chk['feasibility_non_null']})")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
