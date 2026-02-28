"""
Complete Validation Suite for Federal Survey Harmonization Numbers
=================================================================

This script validates EVERY number claimed in the research, end-to-end.
It traces from raw CSV → classification → pairing → rating → question-level → ACS-side,
checking arithmetic, cross-file consistency, round-trip integrity, and document agreement.

Validation levels:
  1. Raw data integrity (Layer 0-1)
  2. Pairing chain integrity (Layer 2-4)
  3. Rating/arbitration consistency (Layer 5)
  4. Question-level dedup correctness (Layer 6)
  5. ACS-side participation (Layer 7)
  6. Arithmetic invariants (sums, rates, totals)
  7. Round-trip spot checks (F1 questions trace back to F1 pairs)
  8. Cross-document consistency (JSON ↔ NUMBERS_MAP ↔ NARRATIVE_CHECKLIST)

Outputs:
  docs/validation/validation_report.json   (machine-readable, all checks)
  docs/validation/validation_report.log    (human-readable summary)

Exit codes:
  0 = all checks pass
  1 = at least one FAIL
  2 = at least one WARN (no FAILs)

Run: python src/validation/validate_complete.py
"""

import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

# =====================================================================
# CONFIGURATION
# =====================================================================
REPO = Path(__file__).resolve().parents[2]

# Source data files
RAW_CSV = REPO / "data" / "raw" / "PublicSurveyQuestionsMap.csv"
QUESTION_LEVEL_CSV = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_question_level.csv"
BEST_MATCHES_CSV = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_question_best_matches.csv"
FINAL_VERDICTS_CSV = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "final_verdicts.csv"
CPS_PAIRS_CSV = REPO / "docs" / "stages" / "02_overlap" / "data" / "question_matching" / "cps" / "cps_candidate_pairs_all.csv"
FOODAPS_PAIRS_CSV = REPO / "docs" / "stages" / "02_overlap" / "data" / "question_matching" / "foodaps" / "foodaps_candidate_pairs_all.csv"
STAGE2_METRICS = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage2_agreement_metrics.json"
STAGE3_METRICS = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage3_arbitration_metrics.json"
SURVEY_SUMMARY_JSON = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_survey_summary.json"
BARRIER_CSV = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "barrier_summary_by_survey.csv"

# Validated reference
QUESTION_COUNTS_JSON = REPO / "docs" / "validation" / "question_counts.json"

# Documents to check
NUMBERS_MAP = REPO / "docs" / "NUMBERS_MAP.md"
NARRATIVE_CHECKLIST = REPO / "report" / "NARRATIVE_CHECKLIST.md"
README = REPO / "README.md"

# Output
OUT_DIR = REPO / "docs" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# TEST FRAMEWORK
# =====================================================================
class ValidationResult:
    def __init__(self, name, status, message, details=None):
        self.name = name
        self.status = status  # PASS, FAIL, WARN, SKIP
        self.message = message
        self.details = details or {}

    def to_dict(self):
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
            "details": self.details,
        }


results = []


def check(name, condition, message, details=None):
    """Register a validation check."""
    status = "PASS" if condition else "FAIL"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name}: {message}")
    return condition


def warn(name, condition, message, details=None):
    """Register a warning (non-fatal)."""
    status = "PASS" if condition else "WARN"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "⚠️"
    print(f"  {icon} {name}: {message}")
    return condition


def skip(name, message, details=None):
    """Skip a check (dependency not met)."""
    r = ValidationResult(name, "SKIP", message, details)
    results.append(r)
    print(f"  ⏭️  {name}: {message}")


def file_exists(path, label):
    """Check file exists, return True/False."""
    return check(
        f"file_exists_{label}",
        path.exists(),
        f"{label}: {'found' if path.exists() else 'MISSING'} at {path.relative_to(REPO)}",
    )


# =====================================================================
# LAYER 0-1: RAW DATA INTEGRITY
# =====================================================================
print("\n" + "=" * 70)
print("LAYER 0-1: RAW DATA INTEGRITY")
print("=" * 70)

if not file_exists(RAW_CSV, "raw_csv"):
    print("FATAL: Cannot continue without raw CSV.")
    sys.exit(1)

raw = pd.read_csv(RAW_CSV)
survey_cols = [c for c in raw.columns if c != "Question" and not c.startswith("Unnamed")]

check(
    "raw_row_count",
    len(raw) == 6987,
    f"Raw CSV row count: {len(raw)} (expected 6987)",
    {"actual": len(raw), "expected": 6987},
)

check(
    "raw_col_count",
    len(survey_cols) == 47,
    f"Survey instrument columns: {len(survey_cols)} (expected 47)",
    {"actual": len(survey_cols), "expected": 47},
)

# Count questions per ACS family survey from raw data
ACS_COL = "American Community Survey (ACS)"
CPS_COL = "Current Population Survey (CPS)"
FOODAPS_COLS = [
    "Food Acquisition and Purchase Survey (FoodAPS) Initial Interview/Household Survey",
    "Food Acquisition and Purchase Survey (FoodAPS) Profile and Income Questionnaire",
    "Food Acquisition and Purchase Survey (FoodAPS) Debriefing Questionnaire",
    "FoodAPS food Log",
]


def has_x(series):
    return series.notna() & (series.astype(str).str.strip() != "")


acs_count = int(has_x(raw[ACS_COL]).sum())
cps_count = int(has_x(raw[CPS_COL]).sum())
food_count = int(raw[FOODAPS_COLS].apply(lambda row: has_x(row).any(), axis=1).sum())

check("acs_raw_count", acs_count == 115, f"ACS raw questions: {acs_count} (expected 115)")
check("cps_raw_count", cps_count == 211, f"CPS raw questions: {cps_count} (expected 211)")
check("foodaps_raw_count", food_count == 462, f"FoodAPS raw questions: {food_count} (expected 462)")

# Literal sharing
acs_mask = has_x(raw[ACS_COL])
cps_mask = has_x(raw[CPS_COL])
food_mask = raw[FOODAPS_COLS].apply(lambda row: has_x(row).any(), axis=1)

acs_cps_shared = int((acs_mask & cps_mask).sum())
acs_food_shared = int((acs_mask & food_mask).sum())
cps_food_shared = int((cps_mask & food_mask).sum())

check("literal_sharing_acs_cps", acs_cps_shared == 0, f"ACS-CPS literal sharing: {acs_cps_shared} (expected 0)")
check("literal_sharing_acs_food", acs_food_shared == 0, f"ACS-FoodAPS literal sharing: {acs_food_shared} (expected 0)")
check("literal_sharing_cps_food", cps_food_shared == 0, f"CPS-FoodAPS literal sharing: {cps_food_shared} (expected 0)")


# =====================================================================
# LAYER 4: PAIRING CHAIN INTEGRITY
# =====================================================================
print("\n" + "=" * 70)
print("LAYER 4: PAIRING CHAIN INTEGRITY")
print("=" * 70)

has_cps_pairs = file_exists(CPS_PAIRS_CSV, "cps_pairs")
has_food_pairs = file_exists(FOODAPS_PAIRS_CSV, "foodaps_pairs")
has_verdicts = file_exists(FINAL_VERDICTS_CSV, "final_verdicts")
has_ql = file_exists(QUESTION_LEVEL_CSV, "question_level")

if has_cps_pairs and has_food_pairs:
    cps_pairs = pd.read_csv(CPS_PAIRS_CSV)
    food_pairs = pd.read_csv(FOODAPS_PAIRS_CSV)

    # candidate_pairs_all files contain ALL generated candidates (pre-filtering)
    # final_verdicts contains only the rated subset (1030 CPS + 568 FoodAPS = 1598)
    # Candidate files should be >= verdict counts (some pairs filtered before rating)
    check(
        "cps_pair_count_gte",
        len(cps_pairs) >= 1030,
        f"CPS candidate pairs: {len(cps_pairs)} (expected >= 1030, rated=1030)",
    )
    check(
        "foodaps_pair_count_gte",
        len(food_pairs) >= 568,
        f"FoodAPS candidate pairs: {len(food_pairs)} (expected >= 568, rated=568)",
    )
    check(
        "total_pair_count_gte",
        len(cps_pairs) + len(food_pairs) >= 1598,
        f"Total candidate pairs: {len(cps_pairs) + len(food_pairs)} (expected >= 1598, rated=1598)",
    )

    # Verify pair IDs are sequential and non-overlapping
    cps_pair_ids = set(cps_pairs["pair_id"])
    food_pair_ids = set(food_pairs["pair_id"])
    check(
        "pair_ids_no_overlap",
        len(cps_pair_ids & food_pair_ids) == 0,
        f"Pair ID overlap: {len(cps_pair_ids & food_pair_ids)} (expected 0)",
    )

    # Verify unique source questions in pairs match expected
    cps_unique_in_pairs = cps_pairs["survey_q_id"].nunique()
    food_unique_in_pairs = food_pairs["survey_q_id"].nunique()
    # Note: these are unique q_ids, not unique texts (q_ids may map to same text)
    check(
        "cps_unique_qids_in_pairs",
        True,  # informational
        f"CPS unique q_ids in pairs: {cps_unique_in_pairs}",
        {"value": cps_unique_in_pairs},
    )
    check(
        "food_unique_qids_in_pairs",
        True,  # informational
        f"FoodAPS unique q_ids in pairs: {food_unique_in_pairs}",
        {"value": food_unique_in_pairs},
    )

    # Verify unique ACS questions in pairs
    cps_acs_in_pairs = cps_pairs["acs_q_id"].nunique()
    food_acs_in_pairs = food_pairs["acs_q_id"].nunique()
    check(
        "cps_acs_in_pairs",
        True,  # informational
        f"Unique ACS q_ids in CPS pairs: {cps_acs_in_pairs}",
    )
    check(
        "food_acs_in_pairs",
        True,  # informational
        f"Unique ACS q_ids in FoodAPS pairs: {food_acs_in_pairs}",
    )

    # Verify all pairs in final_verdicts match candidate pairs
    if has_verdicts:
        fv = pd.read_csv(FINAL_VERDICTS_CSV)
        all_candidate_ids = cps_pair_ids | food_pair_ids
        verdict_ids = set(fv["pair_id"])

        check(
            "verdicts_count",
            len(fv) == 1598,
            f"Final verdicts: {len(fv)} (expected 1598)",
        )
        # Verdicts should be a SUBSET of candidates (some candidates filtered before rating)
        check(
            "verdicts_subset_of_candidates",
            verdict_ids.issubset(all_candidate_ids),
            f"All verdict IDs found in candidate pairs: {verdict_ids.issubset(all_candidate_ids)} ({len(verdict_ids - all_candidate_ids)} orphan verdicts)",
            {
                "in_verdicts_not_candidates": len(verdict_ids - all_candidate_ids),
                "candidates_not_rated": len(all_candidate_ids - verdict_ids),
            },
        )

        # Verify survey assignment in verdicts
        cps_verdict_count = int((fv["survey"] == "CPS").sum())
        food_verdict_count = int((fv["survey"] == "FOODAPS").sum())
        check(
            "verdict_survey_split",
            cps_verdict_count == 1030 and food_verdict_count == 568,
            f"Verdict survey split: CPS={cps_verdict_count}, FoodAPS={food_verdict_count}",
        )

        # Verify feasibility codes are valid
        valid_feas = {"F1", "F2", "F3"}
        actual_feas = set(fv["final_feasibility"].dropna().unique())
        check(
            "valid_feasibility_codes",
            actual_feas.issubset(valid_feas),
            f"Feasibility codes: {actual_feas} (expected subset of {valid_feas})",
        )

        # Pair-level feasibility distribution (for cross-reference)
        fv_cps = fv[fv["survey"] == "CPS"]
        fv_food = fv[fv["survey"] == "FOODAPS"]
        cps_pair_f1 = int((fv_cps["final_feasibility"] == "F1").sum())
        cps_pair_f2 = int((fv_cps["final_feasibility"] == "F2").sum())
        cps_pair_f3 = int((fv_cps["final_feasibility"] == "F3").sum())
        food_pair_f1 = int((fv_food["final_feasibility"] == "F1").sum())
        food_pair_f2 = int((fv_food["final_feasibility"] == "F2").sum())
        food_pair_f3 = int((fv_food["final_feasibility"] == "F3").sum())

        check(
            "pair_feas_sum_cps",
            cps_pair_f1 + cps_pair_f2 + cps_pair_f3 == 1030,
            f"CPS pair feasibility sum: {cps_pair_f1}+{cps_pair_f2}+{cps_pair_f3}={cps_pair_f1+cps_pair_f2+cps_pair_f3} (expected 1030)",
        )
        check(
            "pair_feas_sum_food",
            food_pair_f1 + food_pair_f2 + food_pair_f3 == 568,
            f"FoodAPS pair feasibility sum: {food_pair_f1}+{food_pair_f2}+{food_pair_f3}={food_pair_f1+food_pair_f2+food_pair_f3} (expected 568)",
        )

        # Pair-level consolidation rates
        cps_pair_rate = round(100 * (cps_pair_f1 + cps_pair_f2) / 1030, 1)
        food_pair_rate = round(100 * (food_pair_f1 + food_pair_f2) / 568, 1)
        check(
            "pair_rate_cps",
            abs(cps_pair_rate - 19.5) < 0.5,
            f"CPS pair-level consolidation rate: {cps_pair_rate}% (expected ~19.5%)",
        )
        check(
            "pair_rate_food",
            abs(food_pair_rate - 20.6) < 0.5,
            f"FoodAPS pair-level consolidation rate: {food_pair_rate}% (expected ~20.6%)",
        )


# =====================================================================
# LAYER 5: RATING/ARBITRATION METRICS
# =====================================================================
print("\n" + "=" * 70)
print("LAYER 5: RATING/ARBITRATION METRICS")
print("=" * 70)

has_s2 = file_exists(STAGE2_METRICS, "stage2_metrics")
has_s3 = file_exists(STAGE3_METRICS, "stage3_metrics")

if has_s2:
    with open(STAGE2_METRICS) as f:
        s2 = json.load(f)
    check(
        "s2_total_pairs",
        s2["metadata"]["total_pairs"] == 1598,
        f"Stage 2 total pairs: {s2['metadata']['total_pairs']} (expected 1598)",
    )
    fleiss_feas = s2.get("feasibility_agreement", {}).get("overall", {}).get("three_way", {}).get("fleiss_kappa")
    fleiss_l1 = s2.get("L1_agreement", {}).get("overall", {}).get("three_way", {}).get("fleiss_kappa")
    check(
        "s2_fleiss_feasibility",
        fleiss_feas is not None and abs(fleiss_feas - 0.537) < 0.001,
        f"Stage 2 Fleiss' kappa (feasibility): {fleiss_feas} (expected 0.537)",
    )
    check(
        "s2_fleiss_l1",
        fleiss_l1 is not None and abs(fleiss_l1 - 0.611) < 0.001,
        f"Stage 2 Fleiss' kappa (L1): {fleiss_l1} (expected 0.611)",
    )

if has_s3:
    with open(STAGE3_METRICS) as f:
        s3 = json.load(f)
    check(
        "s3_two_way_n",
        s3["metadata"]["two_way_n"] == 1598,
        f"Stage 3 two-way N: {s3['metadata']['two_way_n']} (expected 1598)",
    )
    cohen_feas = s3.get("two_way_agreement", {}).get("feasibility", {}).get("cohens_kappa")
    cohen_binary = s3.get("two_way_agreement", {}).get("binary_consolidability", {}).get("cohens_kappa")
    check(
        "s3_cohen_feasibility",
        cohen_feas is not None and abs(cohen_feas - 0.843) < 0.001,
        f"Stage 3 Cohen's kappa (feasibility, 2-way): {cohen_feas} (expected 0.843)",
    )
    check(
        "s3_cohen_binary",
        cohen_binary is not None and abs(cohen_binary - 0.896) < 0.001,
        f"Stage 3 Cohen's kappa (binary, 2-way): {cohen_binary} (expected 0.896)",
    )


# =====================================================================
# LAYER 6: QUESTION-LEVEL DEDUP CORRECTNESS
# =====================================================================
print("\n" + "=" * 70)
print("LAYER 6: QUESTION-LEVEL DEDUP CORRECTNESS")
print("=" * 70)

if has_ql:
    ql = pd.read_csv(QUESTION_LEVEL_CSV)
    feas_rank = {"F1": 1, "F2": 2, "F3": 3}

    # Verify corrected row counts (pipeline fixed to dedup by question_text)
    cps_row_count = len(ql[ql["survey"] == "CPS"])
    food_row_count = len(ql[ql["survey"] == "FOODAPS"])
    check(
        "ql_row_count_cps",
        cps_row_count == 157,
        f"stage4_question_level.csv CPS rows: {cps_row_count} (expected 157)",
    )
    check(
        "ql_row_count_foodaps",
        food_row_count == 118,
        f"stage4_question_level.csv FoodAPS rows: {food_row_count} (expected 118)",
    )

    # Perform dedup
    corrected = {}
    for survey_code, label in [("CPS", "CPS"), ("FOODAPS", "FoodAPS")]:
        s = ql[ql["survey"] == survey_code].copy()
        s["feas_rank"] = s["best_feasibility"].map(feas_rank)
        best = (
            s.groupby("question_text")
            .agg(best_rank=("feas_rank", "min"), n_ids=("survey_q_id", "count"))
            .reset_index()
        )
        best["best_feasibility"] = best["best_rank"].map({1: "F1", 2: "F2", 3: "F3"})
        unique_n = len(best)
        f1 = int((best["best_feasibility"] == "F1").sum())
        f2 = int((best["best_feasibility"] == "F2").sum())
        f3 = int((best["best_feasibility"] == "F3").sum())
        corrected[label] = {"unique": unique_n, "F1": f1, "F2": f2, "F3": f3, "best_df": best}

    # Expected values from number_flow.md
    EXPECTED = {
        "CPS": {"unique": 157, "F1": 32, "F2": 54, "F3": 71},
        "FoodAPS": {"unique": 118, "F1": 19, "F2": 37, "F3": 62},
    }

    for label in ["CPS", "FoodAPS"]:
        c = corrected[label]
        e = EXPECTED[label]
        check(
            f"dedup_{label}_unique",
            c["unique"] == e["unique"],
            f"{label} unique questions: {c['unique']} (expected {e['unique']})",
        )
        check(
            f"dedup_{label}_F1",
            c["F1"] == e["F1"],
            f"{label} F1: {c['F1']} (expected {e['F1']})",
        )
        check(
            f"dedup_{label}_F2",
            c["F2"] == e["F2"],
            f"{label} F2: {c['F2']} (expected {e['F2']})",
        )
        check(
            f"dedup_{label}_F3",
            c["F3"] == e["F3"],
            f"{label} F3: {c['F3']} (expected {e['F3']})",
        )

    # ARITHMETIC INVARIANTS
    print("\n  --- Arithmetic invariants ---")
    for label in ["CPS", "FoodAPS"]:
        c = corrected[label]
        total = c["F1"] + c["F2"] + c["F3"]
        check(
            f"arithmetic_{label}_sum",
            total == c["unique"],
            f"{label}: F1+F2+F3 = {c['F1']}+{c['F2']}+{c['F3']} = {total}, unique = {c['unique']}",
        )
        consolidable = c["F1"] + c["F2"]
        rate = round(100 * consolidable / c["unique"], 1)
        exp_rate = EXPECTED[label]
        exp_consolidable = exp_rate["F1"] + exp_rate["F2"]
        exp_rate_val = round(100 * exp_consolidable / exp_rate["unique"], 1)
        check(
            f"arithmetic_{label}_rate",
            abs(rate - exp_rate_val) < 0.1,
            f"{label} rate: {consolidable}/{c['unique']} = {rate}% (expected {exp_rate_val}%)",
        )

    # Combined arithmetic
    total_unique = corrected["CPS"]["unique"] + corrected["FoodAPS"]["unique"]
    total_consolidable = (corrected["CPS"]["F1"] + corrected["CPS"]["F2"] +
                          corrected["FoodAPS"]["F1"] + corrected["FoodAPS"]["F2"])
    check(
        "arithmetic_total_unique",
        total_unique == 275,
        f"Total unique: {total_unique} (expected 275)",
    )
    check(
        "arithmetic_total_consolidable",
        total_consolidable == 142,
        f"Total consolidable: {total_consolidable} (expected 142)",
    )

    # INFLATION CHARACTERIZATION
    print("\n  --- Inflation characterization ---")
    for survey_code, label in [("CPS", "CPS"), ("FOODAPS", "FoodAPS")]:
        s = ql[ql["survey"] == survey_code].copy()
        dup_counts = s.groupby("question_text").size()
        max_dup = int(dup_counts.max())
        n_duplicated = int((dup_counts > 1).sum())
        mean_dup = round(float(dup_counts.mean()), 2)
        check(
            f"inflation_{label}_characterized",
            True,  # informational
            f"{label}: max duplication={max_dup}x, {n_duplicated} questions duplicated, mean={mean_dup}x",
            {"max_dup": max_dup, "n_duplicated": n_duplicated, "mean_dup": mean_dup},
        )


# =====================================================================
# LAYER 7: ACS-SIDE PARTICIPATION
# =====================================================================
print("\n" + "=" * 70)
print("LAYER 7: ACS-SIDE PARTICIPATION")
print("=" * 70)

has_bm = file_exists(BEST_MATCHES_CSV, "best_matches")

if has_bm:
    bm = pd.read_csv(BEST_MATCHES_CSV)

    # Expected: best_match_text column has ACS question text
    if "best_match_text" in bm.columns and "best_feasibility" in bm.columns:
        # ---------------------------------------------------------------
        # ACS-SIDE METHOD: Go through raw pair data (final_verdicts +
        # candidate pair question maps). For each unique consolidable source
        # question text, union all its q_ids (across subtopic contexts), then
        # for each q_id take its best F1/F2 ACS match (by feasibility rank,
        # then Borda score). Union those ACS targets per survey.
        #
        # This method correctly gives 36/32/51 regardless of whether
        # question_level has 380 or 275 rows, because it goes to the raw
        # source of q_id→ACS-target mappings.
        # ---------------------------------------------------------------
        _cps_map_path = REPO / "data" / "processed" / "cps_comparison_merged.csv"
        _food_map_path = REPO / "data" / "processed" / "foodaps_comparison_merged.csv"
        _scores_path = REPO / "docs" / "stages" / "03_harmonization" / "data" / "analysis" / "stage4_bakeoff_scores.csv"

        if _cps_map_path.exists() and _food_map_path.exists():
            _cps_m = pd.read_csv(_cps_map_path, usecols=["pair_id", "survey_q_id", "survey_text", "acs_text"])
            _food_m = pd.read_csv(_food_map_path, usecols=["pair_id", "survey_q_id", "survey_text", "acs_text"])
            _qmap = pd.concat([_cps_m, _food_m], ignore_index=True)
            _fv = pd.read_csv(FINAL_VERDICTS_CSV)
            _pa = _fv.merge(_qmap, on="pair_id", how="left")
            _pa["survey_text_norm"] = _pa["survey_text"].str.strip()
            _pa["_feas_rank"] = _pa["final_feasibility"].map({"F1": 1, "F2": 2, "F3": 3}).fillna(99)
            if _scores_path.exists():
                _sc = pd.read_csv(_scores_path, usecols=["pair_id", "score_borda"])
                _pa = _pa.merge(_sc, on="pair_id", how="left")
            else:
                _pa["score_borda"] = 0
            _pa["score_borda"] = _pa["score_borda"].fillna(0)

            cps_acs_set = set()
            food_acs_set = set()

            for survey_code, acs_set in [("CPS", cps_acs_set), ("FOODAPS", food_acs_set)]:
                _s = _pa[_pa["survey"] == survey_code].copy()
                # Unique texts with at least one F1/F2 pair
                _consol_texts = set(
                    _s[_s["final_feasibility"].isin(["F1", "F2"])]["survey_text_norm"].dropna()
                )
                # All q_ids for consolidable texts
                _consol_qids = set(
                    _s[_s["survey_text_norm"].isin(_consol_texts)]["survey_q_id"]
                )
                # Best ACS target per q_id (best feasibility, then Borda)
                _f12 = _s[
                    _s["survey_q_id"].isin(_consol_qids)
                    & _s["final_feasibility"].isin(["F1", "F2"])
                ].copy()
                _best_per_qid = (
                    _f12.sort_values(["_feas_rank", "score_borda"], ascending=[True, False])
                    .drop_duplicates(subset="survey_q_id", keep="first")
                )
                acs_set.update(_best_per_qid["acs_text"].dropna().unique())

            cps_acs_targets = len(cps_acs_set)
            food_acs_targets = len(food_acs_set)
            all_acs_targets = len(cps_acs_set | food_acs_set)
            three_way = len(cps_acs_set & food_acs_set)
        else:
            # Fallback: use best_matches directly (less precise)
            consolidable_bm = bm[bm["best_feasibility"].isin(["F1", "F2"])]
            cps_bm = consolidable_bm[consolidable_bm["survey"] == "CPS"]
            food_bm = consolidable_bm[consolidable_bm["survey"] == "FOODAPS"]
            cps_acs_targets = cps_bm["best_match_text"].dropna().nunique()
            food_acs_targets = food_bm["best_match_text"].dropna().nunique()
            all_acs_targets = consolidable_bm["best_match_text"].dropna().nunique()
            cps_acs_set = set(cps_bm["best_match_text"].dropna().unique())
            food_acs_set = set(food_bm["best_match_text"].dropna().unique())
            three_way = len(cps_acs_set & food_acs_set)

        check(
            "acs_targets_cps",
            cps_acs_targets == 36,
            f"ACS targets for CPS: {cps_acs_targets} (expected 36)",
        )
        check(
            "acs_targets_foodaps",
            food_acs_targets == 32,
            f"ACS targets for FoodAPS: {food_acs_targets} (expected 32)",
        )
        check(
            "acs_targets_combined",
            all_acs_targets == 51,
            f"Combined unique ACS targets: {all_acs_targets} (expected 51)",
        )
        check(
            "acs_three_way",
            three_way == 17,
            f"Three-way bridge variables: {three_way} (expected 17)",
        )

        # ACS participation rate
        acs_pct = round(100 * all_acs_targets / 115, 1)
        check(
            "acs_participation_rate",
            abs(acs_pct - 44.3) < 0.1,
            f"ACS participation rate: {acs_pct}% (expected 44.3%)",
        )

        # Fan-in ratio
        total_consolidable_for_fanin = 86 + 56  # from corrected counts
        fan_in = round(total_consolidable_for_fanin / all_acs_targets, 2)
        check(
            "acs_fan_in",
            abs(fan_in - 2.78) < 0.01,
            f"Fan-in ratio: {fan_in} (expected 2.78)",
        )

        # Cross-check: unique ACS targets = CPS targets + FoodAPS targets - three-way overlap
        set_arithmetic = cps_acs_targets + food_acs_targets - three_way
        check(
            "acs_set_arithmetic",
            set_arithmetic == all_acs_targets,
            f"Set arithmetic: {cps_acs_targets} + {food_acs_targets} - {three_way} = {set_arithmetic} (expected {all_acs_targets})",
        )
    else:
        skip("acs_side_analysis", f"best_matches columns: {list(bm.columns)}")


# =====================================================================
# ROUND-TRIP SPOT CHECKS
# =====================================================================
print("\n" + "=" * 70)
print("ROUND-TRIP SPOT CHECKS")
print("=" * 70)

if has_ql and has_verdicts and has_cps_pairs:
    fv = pd.read_csv(FINAL_VERDICTS_CSV)
    cps_pairs = pd.read_csv(CPS_PAIRS_CSV)

    # Build text→all_q_ids from candidate pairs (covers all subtopic-context q_ids per text).
    # question_level stores only ONE representative q_id per text; candidate pairs have all of them.
    cps_pairs_txt = cps_pairs.copy()
    cps_pairs_txt["text_norm"] = cps_pairs_txt["survey_text"].str.strip()
    text_to_all_qids = (
        cps_pairs_txt.groupby("text_norm")["survey_q_id"]
        .apply(lambda x: list(x.unique()))
        .to_dict()
    )

    # For each CPS F1 question (after dedup), verify at least one F1 pair exists
    cps_ql = ql[ql["survey"] == "CPS"].copy()
    cps_ql["feas_rank"] = cps_ql["best_feasibility"].map(feas_rank)
    cps_best = (
        cps_ql.groupby("question_text")
        .agg(best_rank=("feas_rank", "min"))
        .reset_index()
    )
    cps_best["best_feas"] = cps_best["best_rank"].map({1: "F1", 2: "F2", 3: "F3"})
    cps_best["q_ids"] = cps_best["question_text"].str.strip().map(text_to_all_qids)

    f1_questions = cps_best[cps_best["best_feas"] == "F1"]

    # Build lookup: survey_q_id -> pair_ids
    qid_to_pairs = defaultdict(list)
    for _, row in cps_pairs.iterrows():
        qid_to_pairs[row["survey_q_id"]].append(row["pair_id"])

    # Build lookup: pair_id -> final feasibility
    pair_to_feas = dict(zip(fv["pair_id"], fv["final_feasibility"]))

    # Check each F1 question traces back to at least one F1 pair
    f1_verified = 0
    f1_failed = []
    for _, row in f1_questions.iterrows():
        q_ids = row["q_ids"]
        pair_ids = []
        for qid in q_ids:
            pair_ids.extend(qid_to_pairs.get(qid, []))
        feas_for_q = [pair_to_feas.get(pid) for pid in pair_ids if pid in pair_to_feas]
        if "F1" in feas_for_q:
            f1_verified += 1
        else:
            f1_failed.append({
                "question_text": row["question_text"][:80],
                "q_ids": q_ids,
                "pair_feasibilities": feas_for_q,
            })

    check(
        "roundtrip_f1_all",
        f1_verified == len(f1_questions),
        f"F1 round-trip: {f1_verified}/{len(f1_questions)} CPS F1 questions trace to F1 pairs",
        {"failed": f1_failed} if f1_failed else {},
    )

    # F2: should have at least one F2 pair but NO F1 pairs
    f2_questions = cps_best[cps_best["best_feas"] == "F2"]
    f2_verified = 0
    f2_has_f1 = 0
    for _, row in f2_questions.iterrows():
        q_ids = row["q_ids"]
        pair_ids = []
        for qid in q_ids:
            pair_ids.extend(qid_to_pairs.get(qid, []))
        feas_for_q = [pair_to_feas.get(pid) for pid in pair_ids if pid in pair_to_feas]
        if "F2" in feas_for_q:
            f2_verified += 1
        if "F1" in feas_for_q:
            f2_has_f1 += 1

    check(
        "roundtrip_f2_all",
        f2_verified == len(f2_questions),
        f"F2 round-trip: {f2_verified}/{len(f2_questions)} CPS F2 questions trace to F2 pairs",
    )
    check(
        "roundtrip_f2_no_f1",
        f2_has_f1 == 0,
        f"F2 integrity: {f2_has_f1} F2-classified questions also have F1 pairs (expected 0 -- if >0, dedup 'best' logic is wrong)",
    )

    # F3: should have NO F1 or F2 pairs at all
    f3_questions = cps_best[cps_best["best_feas"] == "F3"]
    f3_has_consolidable = 0
    for _, row in f3_questions.iterrows():
        q_ids = row["q_ids"]
        pair_ids = []
        for qid in q_ids:
            pair_ids.extend(qid_to_pairs.get(qid, []))
        feas_for_q = [pair_to_feas.get(pid) for pid in pair_ids if pid in pair_to_feas]
        if "F1" in feas_for_q or "F2" in feas_for_q:
            f3_has_consolidable += 1

    check(
        "roundtrip_f3_clean",
        f3_has_consolidable == 0,
        f"F3 integrity: {f3_has_consolidable} F3-classified questions have F1/F2 pairs (expected 0)",
    )

else:
    skip("roundtrip_checks", "Missing required files for round-trip validation")


# =====================================================================
# CROSS-DOCUMENT CONSISTENCY
# =====================================================================
print("\n" + "=" * 70)
print("CROSS-DOCUMENT CONSISTENCY")
print("=" * 70)


# Check question_counts.json matches what we just computed
has_qcj = file_exists(QUESTION_COUNTS_JSON, "question_counts_json")
if has_qcj and has_ql:
    with open(QUESTION_COUNTS_JSON) as f:
        qcj = json.load(f)

    qcj_cps = qcj["question_level_results"]["CPS"]
    qcj_food = qcj["question_level_results"]["FoodAPS"]

    for label, qcj_data in [("CPS", qcj_cps), ("FoodAPS", qcj_food)]:
        c = corrected[label]
        check(
            f"json_match_{label}_unique",
            qcj_data["unique_questions"] == c["unique"],
            f"question_counts.json {label} unique: {qcj_data['unique_questions']} vs computed {c['unique']}",
        )
        check(
            f"json_match_{label}_F1",
            qcj_data["F1"] == c["F1"],
            f"question_counts.json {label} F1: {qcj_data['F1']} vs computed {c['F1']}",
        )
        check(
            f"json_match_{label}_F2",
            qcj_data["F2"] == c["F2"],
            f"question_counts.json {label} F2: {qcj_data['F2']} vs computed {c['F2']}",
        )
        check(
            f"json_match_{label}_F3",
            qcj_data["F3"] == c["F3"],
            f"question_counts.json {label} F3: {qcj_data['F3']} vs computed {c['F3']}",
        )

# Check NUMBERS_MAP has corrected values (not inflated)
has_nm = file_exists(NUMBERS_MAP, "numbers_map")
if has_nm:
    nm_text = NUMBERS_MAP.read_text()

    # Should contain corrected values
    check(
        "nm_has_157",
        "**157**" in nm_text,
        "NUMBERS_MAP contains CPS=157 (bolded)",
    )
    check(
        "nm_has_118",
        "**118**" in nm_text,
        "NUMBERS_MAP contains FoodAPS=118 (bolded)",
    )
    check(
        "nm_has_275",
        "**275**" in nm_text,
        "NUMBERS_MAP contains total=275 (bolded)",
    )
    check(
        "nm_has_54_8",
        "**54.8%**" in nm_text,
        "NUMBERS_MAP contains CPS rate 54.8% (bolded)",
    )
    check(
        "nm_has_47_5",
        "**47.5%**" in nm_text,
        "NUMBERS_MAP contains FoodAPS rate 47.5% (bolded)",
    )

    # Check Step 7 table does NOT have inflated values as current data
    step7_match = re.search(r"### Step 7:.*?### Step 7b:", nm_text, re.DOTALL)
    if step7_match:
        step7_text = step7_match.group(0)
        check(
            "nm_no_inflated_step7",
            "| 240 " not in step7_text and "| 140 " not in step7_text,
            "NUMBERS_MAP Step 7 does not contain inflated values (240/140) as current data",
        )
    else:
        warn("nm_step7_found", False, "Could not isolate NUMBERS_MAP Step 7 section")

    # Check audit date
    check(
        "nm_audit_date",
        "2026-02-28" in nm_text,
        "NUMBERS_MAP audit date includes 2026-02-28",
    )

    # Check Step 7b (ACS-side) exists
    check(
        "nm_has_step7b",
        "Step 7b" in nm_text,
        "NUMBERS_MAP has Step 7b (ACS-side participation)",
    )

# Check NARRATIVE_CHECKLIST has corrected values
has_nc = file_exists(NARRATIVE_CHECKLIST, "narrative_checklist")
if has_nc:
    nc_text = NARRATIVE_CHECKLIST.read_text()

    check(
        "nc_has_corrected_cps_rate",
        "54.8%" in nc_text,
        "NARRATIVE_CHECKLIST contains corrected CPS rate 54.8%",
    )
    check(
        "nc_has_corrected_food_rate",
        "47.5%" in nc_text,
        "NARRATIVE_CHECKLIST contains corrected FoodAPS rate 47.5%",
    )
    check(
        "nc_has_275",
        "275" in nc_text,
        "NARRATIVE_CHECKLIST contains corrected total 275",
    )
    check(
        "nc_has_inflation_warning",
        "INFLATION" in nc_text or "inflation" in nc_text,
        "NARRATIVE_CHECKLIST flags inflation correction",
    )

# Check README
has_readme = file_exists(README, "readme")
if has_readme:
    readme_text = README.read_text()

    check(
        "readme_has_142",
        "142 harmonizable" in readme_text or "142" in readme_text,
        "README contains corrected total 142",
    )
    check(
        "readme_no_stale_154",
        "154 harmonizable" not in readme_text,
        "README does not contain stale '154 harmonizable'",
    )
    check(
        "readme_no_stale_170",
        "170 harmonizable" not in readme_text and "170 consolidable" not in readme_text,
        "README does not contain stale '170'",
    )
    check(
        "readme_no_stale_380",
        "380 unique" not in readme_text and "380 source" not in readme_text,
        "README does not contain stale '380'",
    )


# =====================================================================
# KNOWN INFLATED SOURCE FLAGGING
# =====================================================================
print("\n" + "=" * 70)
print("SURVEY SUMMARY JSON CHECKS")
print("=" * 70)

has_ssj = file_exists(SURVEY_SUMMARY_JSON, "survey_summary_json")
if has_ssj:
    with open(SURVEY_SUMMARY_JSON) as f:
        ssj = json.load(f)

    # Verify survey_summary.json has been regenerated with corrected counts
    check(
        "ssj_cps",
        ssj["CPS"]["total_questions"] == 157,
        f"survey_summary.json CPS: {ssj['CPS']['total_questions']} (expected 157)",
    )
    check(
        "ssj_foodaps",
        ssj["FOODAPS"]["total_questions"] == 118,
        f"survey_summary.json FoodAPS: {ssj['FOODAPS']['total_questions']} (expected 118)",
    )


# =====================================================================
# COMPLETENESS CHECK
# =====================================================================
print("\n" + "=" * 70)
print("FILE COMPLETENESS")
print("=" * 70)

expected_files = {
    "raw_data": RAW_CSV,
    "question_level": QUESTION_LEVEL_CSV,
    "best_matches": BEST_MATCHES_CSV,
    "final_verdicts": FINAL_VERDICTS_CSV,
    "cps_pairs": CPS_PAIRS_CSV,
    "foodaps_pairs": FOODAPS_PAIRS_CSV,
    "stage2_metrics": STAGE2_METRICS,
    "stage3_metrics": STAGE3_METRICS,
    "question_counts_json": QUESTION_COUNTS_JSON,
    "numbers_map": NUMBERS_MAP,
    "narrative_checklist": NARRATIVE_CHECKLIST,
    "number_flow": REPO / "docs" / "validation" / "number_flow.md",
    "validate_counts_script": REPO / "src" / "validation" / "validate_question_counts.py",
    "validate_complete_script": REPO / "src" / "validation" / "validate_complete.py",
}

for label, path in expected_files.items():
    file_exists(path, f"completeness_{label}")


# =====================================================================
# SUMMARY AND OUTPUT
# =====================================================================
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

n_pass = sum(1 for r in results if r.status == "PASS")
n_fail = sum(1 for r in results if r.status == "FAIL")
n_warn = sum(1 for r in results if r.status == "WARN")
n_skip = sum(1 for r in results if r.status == "SKIP")

print(f"\n  Total checks: {len(results)}")
print(f"  PASS: {n_pass}")
print(f"  FAIL: {n_fail}")
print(f"  WARN: {n_warn}")
print(f"  SKIP: {n_skip}")

if n_fail > 0:
    print("\n  FAILED CHECKS:")
    for r in results:
        if r.status == "FAIL":
            print(f"    {r.name}: {r.message}")
            if r.details:
                for k, v in r.details.items():
                    print(f"       {k}: {v}")

if n_warn > 0:
    print("\n  WARNINGS:")
    for r in results:
        if r.status == "WARN":
            print(f"    {r.name}: {r.message}")

# Write JSON report
report = {
    "metadata": {
        "generated": datetime.now().isoformat(),
        "script": "src/validation/validate_complete.py",
        "repo_root": str(REPO),
    },
    "summary": {
        "total": len(results),
        "pass": n_pass,
        "fail": n_fail,
        "warn": n_warn,
        "skip": n_skip,
        "verdict": "PASS" if n_fail == 0 and n_warn == 0 else ("WARN" if n_fail == 0 else "FAIL"),
    },
    "checks": [r.to_dict() for r in results],
}

json_path = OUT_DIR / "validation_report.json"
with open(json_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n  Saved: {json_path}")

# Write log
log_path = OUT_DIR / "validation_report.log"
lines = [
    f"Complete Validation Report -- {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"Script: src/validation/validate_complete.py",
    f"",
    f"VERDICT: {report['summary']['verdict']}",
    f"  PASS={n_pass}  FAIL={n_fail}  WARN={n_warn}  SKIP={n_skip}",
    f"",
]
for r in results:
    icon = {"PASS": "OK", "FAIL": "FAIL", "WARN": "WARN", "SKIP": "SKIP"}[r.status]
    lines.append(f"[{icon}] {r.name}: {r.message}")
    if r.details and r.status != "PASS":
        for k, v in r.details.items():
            lines.append(f"    {k}: {v}")

with open(log_path, "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"  Saved: {log_path}")

# Exit code
if n_fail > 0:
    sys.exit(1)
elif n_warn > 0:
    sys.exit(2)
else:
    sys.exit(0)
