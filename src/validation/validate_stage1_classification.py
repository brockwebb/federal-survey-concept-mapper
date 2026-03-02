"""
Stage 1 Classification V&V — Routing Path Verification
=======================================================

Validates every number in the Stage 1 classification pipeline by tracing
questions through the actual routing paths: agreement → auto_dual_modal → arbitration → reconciliation.

Answers the question: "What EXACTLY went through WHICH pipeline path?"

Layers:
  0: File existence
  1: Input counts
  2: Dual-model comparison (agreement recomputed from raw labels)
  3: Routing paths (consensus / auto_dual_modal / arbitration splits)
  4: Master dataset reconciliation (input→output gap)
  5: Cross-check NUMBERS_MAP
  6: Arithmetic invariants (routing equation)
  7: Kappa applicability (no post-arb κ for Stage 1)
  8: Arbitrator decision counts (GAP-002) — cross-check decision_method vs arb_decision
  9: Dual-modal total verification (GAP-003) — 821 auto + 19 arb = 840, flag match
 10: Model name verification vs config/report_03.yaml (GAP-006) — diagram spec model names
 11: Cohen's κ recomputation from raw labels (GAP-001) — sklearn vs agreement_summary.csv

Sources:
  data/raw/PublicSurveyQuestionsMap.csv                                  (input)
  docs/stages/01_classification/data/comparison/full_comparison.csv       (dual-model comparison)
  docs/stages/01_classification/data/comparison/agreement_summary.csv     (agreement metrics)
  docs/stages/01_classification/data/comparison/disagreements.csv         (disagreeing pairs)
  docs/stages/01_classification/data/arbitration_final/arbitration_results.csv       (arbitrated)
  docs/stages/01_classification/data/arbitration_final/auto_dual_modal_results.csv   (auto dual-modal)
  docs/stages/01_classification/data/arbitration_final/all_disagreement_resolutions.csv (all resolutions)
  docs/stages/01_classification/data/final/master_dataset.csv            (final output)

Outputs:
  docs/validation/stage1_classification_report.json   (machine-readable)
  docs/validation/stage1_classification_report.log    (human-readable)

Exit codes: 0=pass, 1=fail, 2=warn

Run: python src/validation/validate_stage1_classification.py
"""

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml
from sklearn.metrics import cohen_kappa_score

# =====================================================================
# CONFIGURATION
# =====================================================================
REPO = Path(__file__).resolve().parents[2]

# Input
RAW_CSV = REPO / "data" / "raw" / "PublicSurveyQuestionsMap.csv"

# Stage 1 comparison files
COMPARISON_DIR = REPO / "docs" / "stages" / "01_classification" / "data" / "comparison"
FULL_COMPARISON = COMPARISON_DIR / "full_comparison.csv"
AGREEMENT_SUMMARY = COMPARISON_DIR / "agreement_summary.csv"
DISAGREEMENTS = COMPARISON_DIR / "disagreements.csv"

# Stage 1 arbitration files
ARB_DIR = REPO / "docs" / "stages" / "01_classification" / "data" / "arbitration_final"
ARBITRATION_RESULTS = ARB_DIR / "arbitration_results.csv"
AUTO_DUAL_MODAL = ARB_DIR / "auto_dual_modal_results.csv"
ALL_RESOLUTIONS = ARB_DIR / "all_disagreement_resolutions.csv"

# Final output
MASTER_DATASET = REPO / "docs" / "stages" / "01_classification" / "data" / "final" / "master_dataset.csv"

# Reference
NUMBERS_MAP = REPO / "docs" / "NUMBERS_MAP.md"

# Output
OUT_DIR = REPO / "docs" / "validation"
OUT_DIR.mkdir(parents=True, exist_ok=True)


# =====================================================================
# TEST FRAMEWORK (same pattern as validate_complete.py)
# =====================================================================
class ValidationResult:
    def __init__(self, name, status, message, details=None):
        self.name = name
        self.status = status
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
    status = "PASS" if condition else "FAIL"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "❌"
    print(f"  {icon} {name}: {message}")
    return condition


def warn(name, condition, message, details=None):
    status = "PASS" if condition else "WARN"
    r = ValidationResult(name, status, message, details)
    results.append(r)
    icon = "✅" if status == "PASS" else "⚠️"
    print(f"  {icon} {name}: {message}")
    return condition


def skip(name, message, details=None):
    r = ValidationResult(name, "SKIP", message, details)
    results.append(r)
    print(f"  ⏭️  {name}: {message}")


def file_exists(path, label):
    exists = path.exists()
    check(f"file_exists_{label}", exists, f"{label}: {'found' if exists else 'MISSING'} at {path.relative_to(REPO)}")
    return exists


# =====================================================================
# LAYER 0: FILE EXISTENCE
# =====================================================================
print("\n" + "=" * 70)
print("STAGE 1 CLASSIFICATION V&V")
print("=" * 70)

print("\n--- File existence ---")
has_raw = file_exists(RAW_CSV, "raw_csv")
has_comparison = file_exists(FULL_COMPARISON, "full_comparison")
has_agreement = file_exists(AGREEMENT_SUMMARY, "agreement_summary")
has_disagreements = file_exists(DISAGREEMENTS, "disagreements")
has_arb = file_exists(ARBITRATION_RESULTS, "arbitration_results")
has_dual = file_exists(AUTO_DUAL_MODAL, "auto_dual_modal")
has_all_res = file_exists(ALL_RESOLUTIONS, "all_resolutions")
has_master = file_exists(MASTER_DATASET, "master_dataset")

if not (has_raw and has_comparison and has_master):
    print("\nFATAL: Missing critical files. Cannot continue.")
    sys.exit(1)


# =====================================================================
# LAYER 1: INPUT COUNTS
# =====================================================================
print("\n--- Layer 1: Input counts ---")

raw = pd.read_csv(RAW_CSV)
survey_cols = [c for c in raw.columns if c != "Question" and not c.startswith("Unnamed")]
check("input_rows", len(raw) == 6987, f"Input rows (deduplicated): {len(raw)} (expected 6987)")
check("input_surveys", len(survey_cols) == 47, f"Survey instruments: {len(survey_cols)} (expected 47)")


# =====================================================================
# LAYER 2: DUAL-MODEL COMPARISON
# =====================================================================
print("\n--- Layer 2: Dual-model comparison ---")

comp = pd.read_csv(FULL_COMPARISON)
check("comparison_rows", True, f"Full comparison rows: {len(comp)}", {"count": len(comp)})

# Compute agreement at topic and subtopic level from raw comparison.
#
# TWO distinct subtopic metrics (different denominators, different meanings):
#
#   subtopic_only_agree: subtopic labels match regardless of topic (4846/6954 = 69.69%)
#     → This is what agreement_summary.csv stores. Inter-rater label agreement metric.
#
#   subtopic_agree (compound): both topic AND subtopic match (4765/6954 = 68.52%)
#     → This is the ROUTING CRITERION used by the pipeline.
#     → Confirmed: 6954 - 4765 = 2189 = all_disagreement_resolutions.csv rows.
#     → The 81 rows where subtopics match but topics differ went to resolution, not consensus.
comp["topic_agree"] = comp["primary_topic_openai"] == comp["primary_topic_claude"]
comp["subtopic_only_agree"] = (
    comp["primary_subtopic_openai"] == comp["primary_subtopic_claude"]
)
comp["subtopic_agree"] = (
    (comp["primary_topic_openai"] == comp["primary_topic_claude"])
    & (comp["primary_subtopic_openai"] == comp["primary_subtopic_claude"])
)

topic_agree_pct = round(100 * comp["topic_agree"].mean(), 2)
subtopic_only_pct = round(100 * comp["subtopic_only_agree"].mean(), 2)
subtopic_agree_pct = round(100 * comp["subtopic_agree"].mean(), 2)

n_topic_agree = int(comp["topic_agree"].sum())
n_topic_disagree = int((~comp["topic_agree"]).sum())
n_subtopic_only = int(comp["subtopic_only_agree"].sum())
n_subtopic_agree = int(comp["subtopic_agree"].sum())
n_subtopic_disagree = int((~comp["subtopic_agree"]).sum())

check(
    "topic_agreement_pct",
    abs(topic_agree_pct - 89.24) < 0.1,
    f"Topic agreement: {topic_agree_pct}% ({n_topic_agree}/{len(comp)}) (expected ~89.2%)",
    {"pct": topic_agree_pct, "agree": n_topic_agree, "disagree": n_topic_disagree},
)
# Routing criterion: compound (topic AND subtopic). Expected ~68.52%.
check(
    "subtopic_agreement_pct",
    abs(subtopic_agree_pct - 68.52) < 0.1,
    f"Subtopic routing agreement (compound): {subtopic_agree_pct}% ({n_subtopic_agree}/{len(comp)}) (expected ~68.5%)",
    {"pct": subtopic_agree_pct, "agree": n_subtopic_agree, "disagree": n_subtopic_disagree},
)
# Subtopic-only inter-rater agreement (stored in agreement_summary.csv). Expected ~69.69%.
check(
    "subtopic_only_agreement_pct",
    abs(subtopic_only_pct - 69.69) < 0.1,
    f"Subtopic label agreement (subtopic-only): {subtopic_only_pct}% ({n_subtopic_only}/{len(comp)}) (expected ~69.7%)",
    {"pct": subtopic_only_pct, "agree": n_subtopic_only},
)

# Cross-check with agreement_summary.csv
if has_agreement:
    agg = pd.read_csv(AGREEMENT_SUMMARY)
    agg_dict = dict(zip(agg["Metric"], agg["Value"]))
    check(
        "agreement_csv_topic",
        abs(float(agg_dict.get("Topic Agreement %", 0)) - topic_agree_pct) < 0.01,
        f"agreement_summary.csv topic: {agg_dict.get('Topic Agreement %')} vs computed {topic_agree_pct}",
    )
    # agreement_summary.csv stores subtopic-only agreement (69.69%), not the routing criterion.
    check(
        "agreement_csv_subtopic",
        abs(float(agg_dict.get("Subtopic Agreement %", 0)) - subtopic_only_pct) < 0.01,
        f"agreement_summary.csv subtopic: {agg_dict.get('Subtopic Agreement %')} vs subtopic-only computed {subtopic_only_pct}",
    )
    check(
        "kappa_topic",
        True,
        f"Cohen's κ (topics): {agg_dict.get('Cohen' + chr(39) + 's Kappa (Topics)', 'NOT FOUND')}",
        {"value": agg_dict.get("Cohen's Kappa (Topics)")},
    )
    check(
        "kappa_subtopic",
        True,
        f"Cohen's κ (subtopics): {agg_dict.get('Cohen' + chr(39) + 's Kappa (Subtopics)', 'NOT FOUND')}",
        {"value": agg_dict.get("Cohen's Kappa (Subtopics)")},
    )


# =====================================================================
# LAYER 3: ROUTING PATHS — THE CRITICAL SECTION
# =====================================================================
print("\n--- Layer 3: Routing paths (what went where) ---")

# The routing decision is based on SUBTOPIC agreement (the stricter criterion).
# Subtopic agree → consensus path (no arbitration needed)
# Subtopic disagree → goes to resolution (either auto_dual_modal or arbitrator)

n_consensus = n_subtopic_agree
n_to_resolution = n_subtopic_disagree

check(
    "routing_sum",
    n_consensus + n_to_resolution == len(comp),
    f"Routing sum: {n_consensus} consensus + {n_to_resolution} to resolution = {n_consensus + n_to_resolution} (expected {len(comp)})",
)

# Count from disagreements.csv
# NOTE: disagreements.csv is a stale partial artifact (748 rows).
# all_disagreement_resolutions.csv (2,189 rows) is the authoritative source.
# Downgraded to WARN — do not treat this as a FAIL.
if has_disagreements:
    disagree_df = pd.read_csv(DISAGREEMENTS)
    warn(
        "disagreements_count",
        len(disagree_df) == n_to_resolution,
        f"disagreements.csv rows: {len(disagree_df)} vs computed disagreements: {n_to_resolution} "
        f"(STALE ARTIFACT — see all_disagreement_resolutions.csv for authoritative 2,189-row set)",
        {"disagreements_csv": len(disagree_df), "computed": n_to_resolution},
    )

# Count from resolution files
if has_arb:
    arb = pd.read_csv(ARBITRATION_RESULTS)
    n_arbitrated = len(arb)
    check("arbitrated_count", True, f"Arbitrated by claude-sonnet-4-5: {n_arbitrated}", {"count": n_arbitrated})

    # Arbitrator decision breakdown
    if "decision" in arb.columns:
        arb_decisions = arb["decision"].value_counts().to_dict()
        check(
            "arb_decision_breakdown",
            True,
            f"Arbitrator decisions: {dict(arb_decisions)}",
            arb_decisions,
        )
else:
    n_arbitrated = None

if has_dual:
    dual = pd.read_csv(AUTO_DUAL_MODAL)
    n_auto_dual = len(dual)
    check("auto_dual_modal_count", True, f"Auto dual-modal: {n_auto_dual}", {"count": n_auto_dual})
else:
    n_auto_dual = None

if has_all_res:
    all_res = pd.read_csv(ALL_RESOLUTIONS)
    n_all_resolutions = len(all_res)
    check(
        "all_resolutions_count",
        True,
        f"All disagreement resolutions: {n_all_resolutions}",
        {"count": n_all_resolutions},
    )

    # Break down by status
    if "status" in all_res.columns:
        status_counts = all_res["status"].value_counts().to_dict()
        check("resolution_status_breakdown", True, f"Resolution status: {dict(status_counts)}", status_counts)

    # Verify all_resolutions = arbitrated + auto_dual_modal
    if n_arbitrated is not None and n_auto_dual is not None:
        check(
            "resolution_sum",
            n_all_resolutions == n_arbitrated + n_auto_dual,
            f"Resolution sum: {n_arbitrated} arbitrated + {n_auto_dual} auto_dual = {n_arbitrated + n_auto_dual} vs all_resolutions={n_all_resolutions}",
        )

    # Verify all_resolutions == disagreements
    check(
        "resolutions_match_disagreements",
        n_all_resolutions == n_to_resolution,
        f"All resolutions ({n_all_resolutions}) == computed disagreements ({n_to_resolution})",
    )


# =====================================================================
# LAYER 4: MASTER DATASET RECONCILIATION
# =====================================================================
print("\n--- Layer 4: Master dataset reconciliation ---")

master = pd.read_csv(MASTER_DATASET)
n_master = len(master)
check("master_rows", True, f"master_dataset.csv rows: {n_master}", {"count": n_master})

# Check input vs output gap
n_input = len(comp)
n_gap = n_input - n_master
warn(
    "input_output_gap",
    n_gap == 0,
    f"Input→output gap: {n_input} compared - {n_master} in master = {n_gap} missing",
    {"input": n_input, "output": n_master, "gap": n_gap},
)

# If gap > 0, this is the 6987 vs 6954 vs 6949 discrepancy
if n_gap > 0:
    # Check if comparison has more IDs than master
    comp_ids = set(comp["id"])
    master_ids = set(master["id"])
    in_comp_not_master = comp_ids - master_ids
    in_master_not_comp = master_ids - comp_ids
    check(
        "id_gap_detail",
        True,
        f"IDs in comparison but not master: {len(in_comp_not_master)}; in master but not comparison: {len(in_master_not_comp)}",
        {
            "in_comp_not_master_count": len(in_comp_not_master),
            "in_master_not_comp_count": len(in_master_not_comp),
            "in_comp_not_master_sample": sorted(list(in_comp_not_master))[:20],
        },
    )

# Decision method breakdown
if "decision_method" in master.columns:
    dm_counts = master["decision_method"].value_counts().to_dict()
    check("decision_method_breakdown", True, f"Decision methods in master: {dict(dm_counts)}", dm_counts)

# models_agree breakdown
if "models_agree" in master.columns:
    agree_counts = master["models_agree"].value_counts().to_dict()
    check("models_agree_breakdown", True, f"Models agree in master: {dict(agree_counts)}", agree_counts)

# needs_human_review
if "needs_human_review" in master.columns:
    review_counts = master["needs_human_review"].value_counts().to_dict()
    n_human_review = int(master["needs_human_review"].sum()) if master["needs_human_review"].dtype == bool else None
    check("human_review_count", True, f"Flagged for human review: {dict(review_counts)}", review_counts)

# is_dual_modal
if "is_dual_modal" in master.columns:
    dual_counts = master["is_dual_modal"].value_counts().to_dict()
    n_dual_in_master = int(master["is_dual_modal"].sum()) if master["is_dual_modal"].dtype == bool else None
    check("dual_modal_in_master", True, f"Dual-modal in master: {dict(dual_counts)}", dual_counts)

# has final_topic assigned
n_has_topic = int(master["final_topic"].notna().sum())
n_missing_topic = int(master["final_topic"].isna().sum())
check(
    "final_topic_coverage",
    True,
    f"Questions with final_topic: {n_has_topic}, missing: {n_missing_topic}",
    {"has_topic": n_has_topic, "missing_topic": n_missing_topic},
)

# Arbitrator decision breakdown in master
if "arb_decision" in master.columns:
    arb_in_master = master[master["arb_decision"].notna()]
    n_arb_master = len(arb_in_master)
    arb_master_decisions = arb_in_master["arb_decision"].value_counts().to_dict()
    check(
        "arb_decisions_in_master",
        True,
        f"Arbitrated in master: {n_arb_master}, decisions: {dict(arb_master_decisions)}",
        {"count": n_arb_master, "decisions": arb_master_decisions},
    )

# Topic distribution in final
if "final_topic" in master.columns:
    topic_dist = master["final_topic"].value_counts().to_dict()
    check("final_topic_distribution", True, f"Topic distribution: {dict(topic_dist)}", topic_dist)


# =====================================================================
# LAYER 5: CROSS-CHECK NUMBERS_MAP
# =====================================================================
print("\n--- Layer 5: Cross-check NUMBERS_MAP ---")

if NUMBERS_MAP.exists():
    nm = NUMBERS_MAP.read_text()

    # NUMBERS_MAP says 6,954 classified
    check(
        "nm_classified_count",
        "6,954" in nm,
        f"NUMBERS_MAP claims 6,954 classified: {'found' if '6,954' in nm else 'NOT FOUND'}",
    )

    # Check if master matches that claim
    check(
        "master_vs_nm",
        n_master == 6954,
        f"master_dataset.csv rows ({n_master}) vs NUMBERS_MAP claim (6,954)",
        {"master": n_master, "numbers_map_claim": 6954},
    )

    # NUMBERS_MAP says 89.2% topic, 69.7% subtopic
    check(
        "nm_topic_pct",
        "89.2%" in nm or "89.24" in nm,
        "NUMBERS_MAP contains topic agreement ~89.2%",
    )
    check(
        "nm_subtopic_pct",
        "69.7%" in nm or "69.69" in nm,
        "NUMBERS_MAP contains subtopic agreement ~69.7%",
    )


# =====================================================================
# LAYER 6: ARITHMETIC INVARIANTS
# =====================================================================
print("\n--- Layer 6: Arithmetic invariants ---")

# The big equation: consensus + arbitrated + auto_dual_modal + ??? = master rows
# (or = comparison rows, if no questions were dropped)
print(f"\n  ROUTING LEDGER:")
print(f"    Input (full_comparison.csv):           {len(comp)}")
print(f"    Subtopic agree (consensus path):       {n_consensus}")
print(f"    Subtopic disagree (to resolution):     {n_to_resolution}")
if n_arbitrated is not None:
    print(f"      → Arbitrated (claude-sonnet-4-5):    {n_arbitrated}")
if n_auto_dual is not None:
    print(f"      → Auto dual-modal:                   {n_auto_dual}")
print(f"    Output (master_dataset.csv):            {n_master}")
print(f"    Gap (input - output):                   {n_gap}")
print()

# The complete routing equation
if n_arbitrated is not None and n_auto_dual is not None:
    reconstructed = n_consensus + n_arbitrated + n_auto_dual
    check(
        "routing_equation",
        reconstructed == len(comp),
        f"Routing equation: {n_consensus} + {n_arbitrated} + {n_auto_dual} = {reconstructed} (expected {len(comp)})",
        {"consensus": n_consensus, "arbitrated": n_arbitrated, "auto_dual": n_auto_dual, "sum": reconstructed, "expected": len(comp)},
    )

    # Does the routing equation account for master?
    check(
        "routing_vs_master",
        True,
        f"Reconstructed total ({reconstructed}) vs master rows ({n_master}): diff = {reconstructed - n_master}",
        {"reconstructed": reconstructed, "master": n_master, "diff": reconstructed - n_master},
    )


# =====================================================================
# LAYER 7: KAPPA APPLICABILITY CHECK
# =====================================================================
print("\n--- Layer 7: Kappa applicability ---")

# Stage 1 has ONE arbitrator (claude-sonnet-4-5). There is no post-arbitration
# inter-rater reliability to compute. The κ values are PRE-arbitration only.
# This section verifies no post-arbitration κ is being claimed for Stage 1.

check(
    "kappa_is_pre_arb_only",
    True,
    "REMINDER: Stage 1 κ (0.84/0.69) is pre-arbitration agreement between two classifiers. "
    "There is ONE arbitrator — no post-arbitration κ is computable or meaningful.",
)

# Check the diagram spec doesn't claim post-arb kappa
stage1_spec = REPO / "assets" / "diagrams" / "paperbanana" / "stage1_classification_method.txt"
if stage1_spec.exists():
    spec_text = stage1_spec.read_text()
    # Look for kappa references
    has_kappa_084 = "0.84" in spec_text or "0.839" in spec_text
    has_kappa_069 = "0.69" in spec_text or "0.687" in spec_text
    has_kappa_0843 = "0.843" in spec_text
    check(
        "spec_has_pre_arb_kappa",
        has_kappa_084 and has_kappa_069,
        f"Stage 1 spec references pre-arb κ (0.84, 0.69): topic={has_kappa_084}, subtopic={has_kappa_069}",
    )
    check(
        "spec_no_stage4_kappa",
        not has_kappa_0843,
        f"Stage 1 spec does NOT reference Stage 4 κ=0.843: {'CLEAN' if not has_kappa_0843 else 'CONTAMINATED — 0.843 belongs to Stage 4 barrier arbitration'}",
    )


# =====================================================================
# LAYER 8: ARBITRATOR DECISION COUNTS (GAP-002)
# =====================================================================
print("\n--- Layer 8: Arbitrator decision counts (GAP-002) ---")

# Cross-check decision_method counts against arb_decision column in master.
# decision_method reflects the FINAL routing decision.
# arb_decision reflects what the arbitrator SAID (raw output).
# The 5-row gap: 5 rows have arb_decision=pick_haiku45 but
# decision_method=unresolved_disagreement (arbitrator decided, but
# downstream validation overrode to unresolved).

if has_master and "arb_decision" in master.columns and "decision_method" in master.columns:
    # Expected decision_method counts for arbitrator-resolved rows
    arb_dm_expected = {
        "pick_gpt5mini": 522,
        "pick_haiku45": 482,
        "new_concept": 340,
        "dual_modal": 19,
    }
    arb_dm_actual = (
        master[master["decision_method"].isin(arb_dm_expected.keys())]
        ["decision_method"]
        .value_counts()
        .to_dict()
    )
    for decision_type, expected_count in arb_dm_expected.items():
        actual_count = arb_dm_actual.get(decision_type, 0)
        check(
            f"arb_decision_count_{decision_type}",
            actual_count == expected_count,
            f"Arbitrator decision '{decision_type}': {actual_count} (expected {expected_count})",
            {"actual": actual_count, "expected": expected_count},
        )

    # Verify sum of arbitrator decisions
    arb_resolved_sum = sum(arb_dm_actual.get(k, 0) for k in arb_dm_expected)
    check(
        "arb_resolved_total",
        arb_resolved_sum == 1363,
        f"Total arbitrator-resolved: {arb_resolved_sum} (expected 1363)",
        {"sum": arb_resolved_sum},
    )

    # The 5-row gap: rows where arbitrator decided but decision_method
    # was overridden to unresolved_disagreement
    arb_raw_counts = (
        master[master["arb_decision"].notna() & ~master["arb_decision"].isin(["auto_dual_modal"])]
        ["arb_decision"]
        .value_counts()
        .to_dict()
    )
    arb_raw_total = sum(arb_raw_counts.values())
    override_gap = arb_raw_total - arb_resolved_sum
    check(
        "arb_override_gap",
        override_gap == 5,
        f"Arbitrator override gap: {arb_raw_total} raw decisions - {arb_resolved_sum} accepted = {override_gap} overridden to unresolved (expected 5)",
        {"raw_total": arb_raw_total, "accepted": arb_resolved_sum, "overridden": override_gap},
    )

    # Verify the 5 overrides are all pick_haiku45
    overridden_rows = master[
        (master["decision_method"] == "unresolved_disagreement")
        & (master["arb_decision"].notna())
    ]
    n_overridden = len(overridden_rows)
    overridden_decisions = overridden_rows["arb_decision"].value_counts().to_dict()
    check(
        "arb_override_detail",
        n_overridden == 5,
        f"Overridden arbitrator decisions: {n_overridden} rows, decisions: {overridden_decisions}",
        {"count": n_overridden, "decisions": overridden_decisions},
    )
else:
    skip("arb_decision_counts", "Missing master_dataset or required columns")


# =====================================================================
# LAYER 9: DUAL-MODAL TOTAL VERIFICATION (GAP-003)
# =====================================================================
print("\n--- Layer 9: Dual-modal total (GAP-003) ---")

if has_master and "is_dual_modal" in master.columns and "decision_method" in master.columns:
    # Auto dual-modal: from decision_method
    n_auto_dm_master = int((master["decision_method"] == "auto_dual_modal").sum())
    # Arbitrator dual-modal: from decision_method
    n_arb_dm_master = int((master["decision_method"] == "dual_modal").sum())
    # is_dual_modal flag
    n_dm_flag = int(master["is_dual_modal"].sum()) if master["is_dual_modal"].dtype == bool else int((master["is_dual_modal"] == True).sum())

    dm_sum = n_auto_dm_master + n_arb_dm_master

    check(
        "dual_modal_auto",
        n_auto_dm_master == 821,
        f"Auto dual-modal (decision_method): {n_auto_dm_master} (expected 821)",
        {"count": n_auto_dm_master},
    )
    check(
        "dual_modal_arb",
        n_arb_dm_master == 19,
        f"Arbitrator dual-modal (decision_method): {n_arb_dm_master} (expected 19)",
        {"count": n_arb_dm_master},
    )
    check(
        "dual_modal_total",
        dm_sum == 840,
        f"Total dual-modal: {n_auto_dm_master} auto + {n_arb_dm_master} arb = {dm_sum} (expected 840)",
        {"auto": n_auto_dm_master, "arb": n_arb_dm_master, "total": dm_sum},
    )
    check(
        "dual_modal_flag_match",
        n_dm_flag == dm_sum,
        f"is_dual_modal==True ({n_dm_flag}) matches decision_method sum ({dm_sum})",
        {"flag_count": n_dm_flag, "method_sum": dm_sum},
    )
    check(
        "dual_modal_rate",
        True,
        f"Dual-modal rate: {dm_sum}/{n_master} = {round(100*dm_sum/n_master, 1)}% of master",
        {"rate_pct": round(100 * dm_sum / n_master, 1)},
    )
else:
    skip("dual_modal_verification", "Missing master_dataset or required columns")


# =====================================================================
# LAYER 10: MODEL NAME VERIFICATION AGAINST CONFIG (GAP-006 partial)
# =====================================================================
print("\n--- Layer 10: Model name verification vs config ---")

CONFIG_FILE = REPO / "config" / "report_03.yaml"
if CONFIG_FILE.exists():
    with open(CONFIG_FILE) as f:
        cfg = yaml.safe_load(f)

    # Stage 1 uses classifiers (raters from config) + arbitrator
    # Stage 1 arbitrator is claude-sonnet-4-5, which is NOT in report_03.yaml
    # (report_03.yaml covers Stage 3/4 raters and arbitrators)
    # So we verify Stage 3/4 model names against diagram specs

    # Extract rater model names from config
    config_raters = {}
    for vendor, info in cfg.get("raters", {}).items():
        config_raters[vendor] = info.get("model", "")

    config_arbitrators = {}
    for vendor, info in cfg.get("arbitrators", {}).items():
        config_arbitrators[vendor] = info.get("model", "")

    check(
        "config_raters_loaded",
        len(config_raters) == 3,
        f"Config rater models: {config_raters}",
        config_raters,
    )
    check(
        "config_arbitrators_loaded",
        len(config_arbitrators) == 3,
        f"Config arbitrator models: {config_arbitrators}",
        config_arbitrators,
    )

    # Verify NUMBERS_MAP does NOT say "Same models in arbitrator role"
    # (it should list the actual different models)
    if NUMBERS_MAP.exists():
        nm_text = NUMBERS_MAP.read_text()
        has_same_models_claim = "Same models in arbitrator role" in nm_text or "same models" in nm_text.lower().split("arbitrator")[0] if "arbitrator" in nm_text.lower() else False
        # Check if arbitrators differ from raters
        rater_set = set(config_raters.values())
        arb_set = set(config_arbitrators.values())
        models_differ = rater_set != arb_set

        if models_differ:
            check(
                "nm_arbitrator_models_accurate",
                "Same models" not in nm_text.split("Arbitrator models")[0] if "Arbitrator models" in nm_text else True,
                f"Config shows arbitrators DIFFER from raters. "
                f"Raters: {sorted(rater_set)}. Arbitrators: {sorted(arb_set)}. "
                f"NUMBERS_MAP must reflect this distinction.",
                {"raters": sorted(rater_set), "arbitrators": sorted(arb_set), "differ": True},
            )

    def strip_model_suffixes(name):
        """Strip -preview and -YYYYMMDD suffixes to get the display stem."""
        s = name
        if s.endswith("-preview"):
            s = s[: -len("-preview")]
        # Strip date suffixes like -20251001
        if len(s) > 9 and s[-9] == "-" and s[-8:].isdigit():
            s = s[:-9]
        return s

    # Check stage3 diagram spec model names against config
    stage3_spec = REPO / "assets" / "diagrams" / "paperbanana" / "stage3_rating_method.txt"
    if stage3_spec.exists():
        s3_text = stage3_spec.read_text()
        for vendor, model in config_raters.items():
            model_stem = strip_model_suffixes(model)
            found = model in s3_text or model_stem in s3_text
            check(
                f"stage3_spec_model_{vendor}",
                found,
                f"Stage 3 spec contains {vendor} rater model '{model}' (or stem '{model_stem}'): {'found' if found else 'NOT FOUND'}",
                {"vendor": vendor, "config_model": model, "stem": model_stem, "found": found},
            )

    # Check stage4 diagram spec arbitrator names against config
    stage4_spec = REPO / "assets" / "diagrams" / "paperbanana" / "stage4_arbitration_method.txt"
    if stage4_spec.exists():
        s4_text = stage4_spec.read_text()
        for vendor, model in config_arbitrators.items():
            model_stem = strip_model_suffixes(model)
            found = model in s4_text or model_stem in s4_text
            check(
                f"stage4_spec_model_{vendor}",
                found,
                f"Stage 4 spec contains {vendor} arbitrator model '{model}' (or stem '{model_stem}'): {'found' if found else 'NOT FOUND'}",
                {"vendor": vendor, "config_model": model, "stem": model_stem, "found": found},
            )
else:
    skip("config_model_verification", f"Config file not found: {CONFIG_FILE}")


# =====================================================================
# LAYER 11: COHEN'S κ RECOMPUTATION FROM RAW LABELS (GAP-001)
# =====================================================================
print("\n--- Layer 11: Cohen's κ recomputation (GAP-001) ---")

# Recompute kappa independently from raw label columns in full_comparison.csv
# using sklearn, then cross-check against agreement_summary.csv.
# This closes GAP-001: stored kappa values were never independently verified.

if has_comparison and has_agreement:
    # Drop rows where either model has NaN labels (sklearn requires complete pairs)
    topic_pairs = comp[["primary_topic_openai", "primary_topic_claude"]].dropna()
    subtopic_pairs = comp[["primary_subtopic_openai", "primary_subtopic_claude"]].dropna()

    kappa_topic_recomputed = cohen_kappa_score(
        topic_pairs["primary_topic_openai"],
        topic_pairs["primary_topic_claude"],
    )
    kappa_subtopic_recomputed = cohen_kappa_score(
        subtopic_pairs["primary_subtopic_openai"],
        subtopic_pairs["primary_subtopic_claude"],
    )

    print(f"  Recomputed κ (topics):    {kappa_topic_recomputed:.6f}")
    print(f"  Recomputed κ (subtopics): {kappa_subtopic_recomputed:.6f}")

    # Load stored values from agreement_summary.csv
    agg_kappa = pd.read_csv(AGREEMENT_SUMMARY)
    agg_kappa_dict = dict(zip(agg_kappa["Metric"], agg_kappa["Value"]))
    stored_kappa_topic = float(agg_kappa_dict.get("Cohen's Kappa (Topics)", float("nan")))
    stored_kappa_subtopic = float(agg_kappa_dict.get("Cohen's Kappa (Subtopics)", float("nan")))

    print(f"  Stored  κ (topics):    {stored_kappa_topic:.6f}")
    print(f"  Stored  κ (subtopics): {stored_kappa_subtopic:.6f}")

    # Tolerance: ±0.005 (rounding artifacts only)
    TOL = 0.005

    check(
        "kappa_topic_recomputed",
        abs(kappa_topic_recomputed - stored_kappa_topic) <= TOL,
        f"κ topics recomputed ({kappa_topic_recomputed:.4f}) vs stored ({stored_kappa_topic:.4f}): "
        f"diff={abs(kappa_topic_recomputed - stored_kappa_topic):.4f} (tol {TOL})",
        {
            "recomputed": round(kappa_topic_recomputed, 6),
            "stored": stored_kappa_topic,
            "diff": round(abs(kappa_topic_recomputed - stored_kappa_topic), 6),
        },
    )
    check(
        "kappa_subtopic_recomputed",
        abs(kappa_subtopic_recomputed - stored_kappa_subtopic) <= TOL,
        f"κ subtopics recomputed ({kappa_subtopic_recomputed:.4f}) vs stored ({stored_kappa_subtopic:.4f}): "
        f"diff={abs(kappa_subtopic_recomputed - stored_kappa_subtopic):.4f} (tol {TOL})",
        {
            "recomputed": round(kappa_subtopic_recomputed, 6),
            "stored": stored_kappa_subtopic,
            "diff": round(abs(kappa_subtopic_recomputed - stored_kappa_subtopic), 6),
        },
    )

    # Cross-check against NUMBERS_MAP cited values (0.839 topics, 0.687 subtopics)
    check(
        "kappa_topic_vs_nm",
        abs(kappa_topic_recomputed - 0.839) <= TOL,
        f"κ topics recomputed ({kappa_topic_recomputed:.4f}) vs NUMBERS_MAP (0.839): "
        f"diff={abs(kappa_topic_recomputed - 0.839):.4f}",
        {"recomputed": round(kappa_topic_recomputed, 4), "nm_claim": 0.839},
    )
    check(
        "kappa_subtopic_vs_nm",
        abs(kappa_subtopic_recomputed - 0.687) <= TOL,
        f"κ subtopics recomputed ({kappa_subtopic_recomputed:.4f}) vs NUMBERS_MAP (0.687): "
        f"diff={abs(kappa_subtopic_recomputed - 0.687):.4f}",
        {"recomputed": round(kappa_subtopic_recomputed, 4), "nm_claim": 0.687},
    )
else:
    skip("kappa_recomputation", "Missing full_comparison.csv or agreement_summary.csv")


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
        "script": "src/validation/validate_stage1_classification.py",
        "purpose": "Stage 1 classification routing path verification",
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
    "routing_ledger": {
        "input_comparison_rows": len(comp),
        "consensus_path": n_consensus,
        "to_resolution": n_to_resolution,
        "arbitrated": n_arbitrated,
        "auto_dual_modal": n_auto_dual,
        "master_output_rows": n_master,
        "gap": n_gap,
    },
    "checks": [r.to_dict() for r in results],
}

json_path = OUT_DIR / "stage1_classification_report.json"
with open(json_path, "w") as f:
    json.dump(report, f, indent=2)
print(f"\n  Saved: {json_path}")

log_path = OUT_DIR / "stage1_classification_report.log"
lines = [
    f"Stage 1 Classification V&V Report -- {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    f"Script: src/validation/validate_stage1_classification.py",
    f"",
    f"VERDICT: {report['summary']['verdict']}",
    f"  PASS={n_pass}  FAIL={n_fail}  WARN={n_warn}  SKIP={n_skip}",
    f"",
    f"ROUTING LEDGER:",
    f"  Input:          {len(comp)}",
    f"  Consensus:      {n_consensus}",
    f"  To resolution:  {n_to_resolution}",
    f"  Arbitrated:     {n_arbitrated}",
    f"  Auto dual-modal:{n_auto_dual}",
    f"  Master output:  {n_master}",
    f"  Gap:            {n_gap}",
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

if n_fail > 0:
    sys.exit(1)
elif n_warn > 0:
    sys.exit(2)
else:
    sys.exit(0)
