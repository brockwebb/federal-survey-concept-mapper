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

Run from v2/ (the AHS data lives on WORK only; authored on DEV, run on WORK):
    python src/core/stage3_ahs_rollup.py
    python src/core/stage3_ahs_rollup.py --ahs-dir output/stage3/results/ahs
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
CANDIDATE_COLS = [
    "pair_id", "final_feasibility", "shared_subtopic", "survey_text",
    "acs_text", "final_primary_barrier", "final_confidence", "decision_method",
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
        "total_pairs": n_total,
        "candidate_definition": "final_feasibility in {F1, F2}; discard = F3",
        "feasibility_tiers": {
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
    L: list[str] = []

    L.append("# AHS Harmonization Candidate Rollup")
    L.append("")
    L.append(f"Source: `{s['input_path']}` (read {s['encoding']}); the numbers "
             f"in this document are read from `ahs_candidate_summary.json` and "
             f"none are hardcoded here.")
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
    L.append("## Feasibility tiers")
    L.append("")
    L.append("| tier | count | share |")
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
    ap.add_argument("--f2-cap", type=int, default=F2_LIST_CAP,
                    help="cap the F2 listing in the MD (CSV is never capped)")
    args = ap.parse_args()

    ahs_dir = Path(args.ahs_dir)
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
    print(f"  wrote: {out_json}")
    print(f"  wrote: {out_csv}  ({len(cand)} candidates)")
    print(f"  wrote: {out_md}")
    print("\n" + "=" * 70)
    print("HEADLINE")
    print("=" * 70)
    print(f"  total pairs:      {summary['total_pairs']}")
    print(f"  candidates (F1+F2): {tiers['candidate_count']} "
          f"({tiers['candidate_pct']}%)")
    print(f"  F1 / F2 / F3:     {tiers['F1']} / {tiers['F2']} / {tiers['F3']}")
    print(f"  discard (F3):     {tiers['discard_count']} ({tiers['discard_pct']}%)")
    print(f"  {CHECK_PAIR_ID} present: {chk['present']} "
          f"(feasibility non-null: {chk['feasibility_non_null']})")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
