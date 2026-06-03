#!/usr/bin/env python3
"""v1 vs v2 Stage 3 SIGNAL-STRATIFIED reproducibility (CPS + FoodAPS).

Companion to stage3_v1_v2_compare.py. That script measures flat, all-pairs
agreement and finds only moderate barrier-label kappa (CPS L1 k=0.52). But
that number is contaminated: most candidate pairs are "cannon fodder" --
two questions sharing a subtopic that obviously do not harmonize. For those,
"different construct / not feasible" (CC / F3) is the CORRECT answer, and the
two model generations bicker over which flavor of "no" to stamp on a pair
nobody will ever harmonize. That disagreement is real in the kappa and
meaningless for the deliverable.

The deliverable is the HARMONIZATION CANDIDATE LIST. So the metric that
matters is: do v1 and v2 agree on the SIGNAL pairs -- the ones either version
judged harmonizable (feasibility F1/F2)? This script answers that.

It reports, per survey and combined:
  1. Binary candidate-vs-discard agreement + kappa (the metric that matters).
     A pair is a "candidate" if feasibility is F1 or F2; "discard" if F3.
  2. The INTERSECTION set -- pairs BOTH versions independently flag as
     harmonizable. This is the reproducible, defensible candidate list.
  3. Demotions -- v1 candidates that v2 dropped to F3 (the conservatism gap).
  4. Additions -- v2 candidates that v1 had discarded.
  5. A confidence-gated GOLD set -- intersection pairs where BOTH versions
     were also high-confidence (v1 confidence == HIGH; v2 final_confidence
     >= threshold). Each version is gated by its own confidence scheme; the
     schemes are not directly comparable, which the report states plainly.

Join key is the normalized question-text pair (v1/v2 ids are incompatible
schemes). Normalization is duplicated verbatim from stage3_v1_v2_compare.py
so the two scripts produce byte-identical join keys with zero import coupling.

Pure data step -- no API calls, no harness.

Run from v2/:
    python src/core/stage3_v1_v2_signal_stratified.py
    python src/core/stage3_v1_v2_signal_stratified.py --surveys cps
    python src/core/stage3_v1_v2_signal_stratified.py --v2-conf-threshold 0.8
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from sklearn.metrics import cohen_kappa_score
    _HAVE_SK = True
except Exception:  # pragma: no cover
    _HAVE_SK = False


# =============================================================================
# PATHS (defaults assume cwd == v2/)
# =============================================================================

V1_VERDICTS = Path("../docs/stages/03_harmonization/data/analysis/final_verdicts.csv")
V1_PAIRS = {
    "cps": Path("../docs/stages/02_overlap/data/question_matching/cps/cps_candidate_pairs_all.csv"),
    "foodaps": Path("../docs/stages/02_overlap/data/question_matching/foodaps/foodaps_candidate_pairs_all.csv"),
}
V2_RESULTS_DIR = Path("output/stage3/results")
OUT_DIR = Path("output/stage3/v1_v2_comparison")
V1_SURVEY_VALUE = {"cps": "CPS", "foodaps": "FOODAPS"}

CANDIDATE_FEAS = {"F1", "F2"}  # F3 = discard


def die(msg: str) -> None:
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


# =============================================================================
# TEXT NORMALIZATION  (verbatim from stage3_v1_v2_compare.py -- do not drift)
# =============================================================================

_MOJIBAKE = {
    "\u00e2\u20ac\u2122": "'",
    "\u00e2\u20ac\u02dc": "'",
    "\u00e2\u20ac\u0153": '"',
    "\u00e2\u20ac\u009d": '"',
    "\u00e2\u20ac\u201d": "-",
    "\u00e2\u20ac\u201c": "-",
    "\u00e2\u20ac\u00a6": "...",
    "\u00e2\u20ac": '"',
    "\u00c2\u00a0": " ",
}
_FILL_RE = re.compile(r"\[[^\]]*\]")
_PAREN_FILL_RE = re.compile(r"\([^)]*fill[^)]*\)", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")


def _fix_mojibake(s: str) -> str:
    for bad, good in _MOJIBAKE.items():
        if bad in s:
            s = s.replace(bad, good)
    if "\u00e2" in s or "\u00c2" in s:
        try:
            s = s.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            pass
    return s


def normalize_text(v: Any) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v)
    s = _fix_mojibake(s)
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    s = s.replace("\u201c", '"').replace("\u201d", '"')
    s = s.replace("\u2014", "-").replace("\u2013", "-")
    s = _FILL_RE.sub(" ", s)
    s = _PAREN_FILL_RE.sub(" ", s)
    s = s.lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


def pair_key(src: Any, acs: Any) -> str:
    return normalize_text(src) + " ||| " + normalize_text(acs)


# =============================================================================
# HELPERS
# =============================================================================

def kappa(a: pd.Series, b: pd.Series) -> float | None:
    if not _HAVE_SK:
        return None
    try:
        return round(float(cohen_kappa_score(
            a.fillna("NONE").astype(str), b.fillna("NONE").astype(str))), 4)
    except Exception:
        return None


def feas_tier(feas: Any, l1: Any) -> str:
    """direct (F1 or no-barrier), adjustable (F2), discard (F3/other)."""
    f = ("" if feas is None or (isinstance(feas, float) and pd.isna(feas))
         else str(feas).strip().upper())
    code = ("" if l1 is None or (isinstance(l1, float) and pd.isna(l1))
            else str(l1).strip().upper())
    if f == "F1" or code == "NHB":
        return "direct"
    if f == "F2":
        return "adjustable"
    return "discard"


def is_candidate(tier: str) -> bool:
    return tier != "discard"


def _dedup(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    before = len(df)
    df = df[df["pair_key"].str.strip(" |") != ""]
    df = df.drop_duplicates(subset=["pair_key"], keep="first").reset_index(drop=True)
    return df, before - len(df)


# =============================================================================
# LOADERS (include confidence, unlike the flat-compare script)
# =============================================================================

def load_v1(survey_key: str) -> pd.DataFrame:
    pairs_path = V1_PAIRS[survey_key]
    if not pairs_path.exists():
        die(f"v1 pairs not found: {pairs_path.resolve()}")
    if not V1_VERDICTS.exists():
        die(f"v1 verdicts not found: {V1_VERDICTS.resolve()}")

    pairs = pd.read_csv(pairs_path, encoding="utf-8")
    for c in ("pair_id", "survey_text", "acs_text"):
        if c not in pairs.columns:
            die(f"v1 pairs {pairs_path.name} missing {c!r}")

    verdicts = pd.read_csv(V1_VERDICTS, encoding="utf-8")
    for c in ("pair_id", "survey", "final_L1", "final_feasibility"):
        if c not in verdicts.columns:
            die(f"v1 verdicts missing {c!r}")
    has_conf = "confidence" in verdicts.columns
    keep = ["pair_id", "final_L1", "final_feasibility"] + (["confidence"] if has_conf else [])
    verdicts = verdicts[verdicts["survey"] == V1_SURVEY_VALUE[survey_key]][keep].copy()

    df = pairs.merge(verdicts, on="pair_id", how="inner")
    df["pair_key"] = [pair_key(s, a) for s, a in zip(df["survey_text"], df["acs_text"])]
    df["v1_conf_high"] = (
        df["confidence"].astype(str).str.upper().eq("HIGH") if has_conf else False
    )
    df = df.rename(columns={
        "pair_id": "v1_pair_id",
        "final_L1": "v1_L1",
        "final_feasibility": "v1_feas",
    })
    df["v1_tier"] = [feas_tier(f, l) for f, l in zip(df["v1_feas"], df["v1_L1"])]
    return df[["pair_key", "v1_pair_id", "v1_L1", "v1_feas", "v1_tier",
               "v1_conf_high", "survey_text", "acs_text"]]


def load_v2(survey_key: str, conf_threshold: float) -> pd.DataFrame:
    final_path = V2_RESULTS_DIR / survey_key / "final_barrier_classifications.csv"
    if not final_path.exists():
        die(f"v2 final not found: {final_path.resolve()}")

    final = pd.read_csv(final_path, encoding="utf-8")
    needed = ["pair_id", "survey_text", "acs_text",
              "final_classification", "final_feasibility"]
    missing = [c for c in needed if c not in final.columns]
    if missing:
        die(f"v2 final missing {missing}; have {list(final.columns)}")
    has_conf = "final_confidence" in final.columns

    cols = needed + (["final_confidence"] if has_conf else [])
    df = final[cols].copy()
    df["pair_key"] = [pair_key(s, a) for s, a in zip(df["survey_text"], df["acs_text"])]
    if has_conf:
        df["v2_conf_high"] = pd.to_numeric(
            df["final_confidence"], errors="coerce").fillna(0.0) >= conf_threshold
    else:
        df["v2_conf_high"] = False
    df = df.rename(columns={
        "pair_id": "v2_pair_id",
        "final_classification": "v2_L1",
        "final_feasibility": "v2_feas",
    })
    df["v2_tier"] = [feas_tier(f, l) for f, l in zip(df["v2_feas"], df["v2_L1"])]
    return df[["pair_key", "v2_pair_id", "v2_L1", "v2_feas", "v2_tier",
               "v2_conf_high"]]


# =============================================================================
# CORE COMPARISON
# =============================================================================

def compare_survey(survey_key: str, conf_threshold: float) -> dict[str, Any]:
    v1, _ = _dedup(load_v1(survey_key))
    v2, _ = _dedup(load_v2(survey_key, conf_threshold))

    common = set(v1["pair_key"]) & set(v2["pair_key"])
    if not common:
        die(f"[{survey_key}] zero common pairs -- normalization is wrong.")

    m = v1.merge(v2, on="pair_key", how="inner")
    m["v1_cand"] = m["v1_tier"].map(is_candidate)
    m["v2_cand"] = m["v2_tier"].map(is_candidate)

    both_cand = m[m["v1_cand"] & m["v2_cand"]].copy()      # intersection (deliverable)
    demoted = m[m["v1_cand"] & ~m["v2_cand"]].copy()       # v1 cand -> v2 discard
    added = m[~m["v1_cand"] & m["v2_cand"]].copy()          # v2 cand, v1 discard
    both_discard = m[~m["v1_cand"] & ~m["v2_cand"]]

    n = len(m)
    n_v1c = int(m["v1_cand"].sum())
    n_v2c = int(m["v2_cand"].sum())
    n_int = len(both_cand)
    union_c = n_v1c + n_v2c - n_int

    # binary candidate-vs-discard kappa (the metric that matters)
    bin_kappa = kappa(m["v1_cand"].map({True: "cand", False: "discard"}),
                      m["v2_cand"].map({True: "cand", False: "discard"}))
    bin_agree = round(float((m["v1_cand"] == m["v2_cand"]).mean()) * 100, 2)

    # on the intersection, do they agree on tier + barrier?
    tier_agree = round(float(
        (both_cand["v1_tier"] == both_cand["v2_tier"]).mean()) * 100, 2) if n_int else 0.0
    l1_agree_on_int = round(float(
        (both_cand["v1_L1"].astype(str) == both_cand["v2_L1"].astype(str)).mean()
    ) * 100, 2) if n_int else 0.0

    # gold set: intersection AND both high-confidence
    gold = both_cand[both_cand["v1_conf_high"] & both_cand["v2_conf_high"]].copy()

    return {
        "survey": survey_key,
        "summary": {
            "n_common_pairs": n,
            "v1_candidates": n_v1c,
            "v2_candidates": n_v2c,
            "intersection_candidates": n_int,
            "candidate_jaccard": round(n_int / union_c, 4) if union_c else 0.0,
            "v1_retained_pct": round(n_int / n_v1c * 100, 2) if n_v1c else 0.0,
            "v2_new_pct": round(len(added) / n_v2c * 100, 2) if n_v2c else 0.0,
            "demoted_count": len(demoted),
            "added_count": len(added),
            "both_discard": len(both_discard),
            "binary_candidate_agreement_pct": bin_agree,
            "binary_candidate_kappa": bin_kappa,
            "tier_agreement_on_intersection_pct": tier_agree,
            "l1_agreement_on_intersection_pct": l1_agree_on_int,
            "gold_count": len(gold),
        },
        "_both_cand": both_cand,
        "_demoted": demoted,
        "_added": added,
        "_gold": gold,
        "_binary_conf": pd.crosstab(
            m["v1_cand"].map({True: "candidate", False: "discard"}),
            m["v2_cand"].map({True: "candidate", False: "discard"}),
            margins=True),
        "_tier_conf": pd.crosstab(m["v1_tier"], m["v2_tier"], margins=True),
    }


# =============================================================================
# REPORT
# =============================================================================

_OUT_COLS = ["pair_key", "v1_pair_id", "v2_pair_id", "v1_L1", "v2_L1",
             "v1_feas", "v2_feas", "v1_tier", "v2_tier",
             "v1_conf_high", "v2_conf_high", "survey_text", "acs_text"]


def write_report(results: list[dict[str, Any]], combined: dict[str, Any],
                 conf_threshold: float, out_dir: Path) -> Path:
    L: list[str] = []
    L.append("# v1 vs v2 Stage 3 Signal-Stratified Reproducibility")
    L.append("")
    L.append("Flat all-pairs barrier kappa is contaminated by disagreement on")
    L.append("discard pairs (cannon fodder both versions reject, bickering only")
    L.append("over which 'no' to apply). This report measures reproducibility of")
    L.append("the thing that matters: the harmonization CANDIDATE list.")
    L.append("")
    L.append("Candidate = feasibility F1 or F2 (or barrier NHB). Discard = F3.")
    L.append(f"v2 high-confidence threshold: final_confidence >= {conf_threshold}.")
    L.append("v1 high-confidence: verdict confidence == HIGH. The two confidence")
    L.append("schemes are NOT directly comparable; each version is gated by its own.")
    L.append("AHS excluded (no v1 baseline).")
    L.append("")

    for r in results:
        s = r["survey"].upper()
        x = r["summary"]
        L.append(f"## {s}")
        L.append("")
        L.append("### What matters: candidate-vs-discard")
        L.append(f"- common pairs: {x['n_common_pairs']:,}")
        L.append(f"- binary candidate agreement: {x['binary_candidate_agreement_pct']}%  "
                 f"(kappa={x['binary_candidate_kappa']})")
        L.append(f"- v1 candidates: {x['v1_candidates']}  |  "
                 f"v2 candidates: {x['v2_candidates']}")
        L.append(f"- INTERSECTION (both flag harmonizable): "
                 f"{x['intersection_candidates']}  "
                 f"(candidate Jaccard {x['candidate_jaccard']:.3f})")
        L.append(f"- v1 candidates retained by v2: {x['v1_retained_pct']}%")
        L.append(f"- v2 demoted to discard: {x['demoted_count']}  |  "
                 f"v2 newly added: {x['added_count']}")
        L.append(f"- GOLD set (intersection + both high-confidence): "
                 f"{x['gold_count']}")
        L.append("")
        L.append("### Agreement WITHIN the intersection")
        L.append(f"- feasibility-tier agreement: "
                 f"{x['tier_agreement_on_intersection_pct']}%")
        L.append(f"- barrier L1 agreement: "
                 f"{x['l1_agreement_on_intersection_pct']}%")
        L.append("")
        L.append("### Binary candidate confusion (v1 rows x v2 cols)")
        L.append("```")
        L.append(r["_binary_conf"].to_string())
        L.append("```")
        L.append("")
        L.append("### Feasibility-tier confusion (v1 rows x v2 cols)")
        L.append("```")
        L.append(r["_tier_conf"].to_string())
        L.append("```")
        L.append("")

    if combined:
        L.append("## COMBINED (CPS + FoodAPS)")
        L.append("")
        L.append(f"- binary candidate agreement: "
                 f"{combined['binary_candidate_agreement_pct']}%  "
                 f"(kappa={combined['binary_candidate_kappa']})")
        L.append(f"- total intersection candidates: "
                 f"{combined['intersection_candidates']}")
        L.append(f"- total gold candidates: {combined['gold_count']}")
        L.append(f"- v1 candidates retained: {combined['v1_retained_pct']}%")
        L.append("")

    path = out_dir / "v1_v2_signal_stratified_report.md"
    path.write_text("\n".join(L), encoding="utf-8")
    return path


# =============================================================================
# MAIN
# =============================================================================

def main() -> int:
    ap = argparse.ArgumentParser(
        description="v1 vs v2 Stage 3 signal-stratified reproducibility")
    ap.add_argument("--surveys", default="cps,foodaps")
    ap.add_argument("--v2-conf-threshold", type=float, default=0.9,
                    help="v2 final_confidence >= this counts as high-confidence")
    args = ap.parse_args()
    keys = [k.strip() for k in args.surveys.split(",") if k.strip()]
    for k in keys:
        if k not in V1_PAIRS:
            die(f"survey {k!r} has no v1 baseline. Valid: {list(V1_PAIRS)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print("v1 vs v2 STAGE 3 SIGNAL-STRATIFIED REPRODUCIBILITY")
    print("=" * 70)
    if not _HAVE_SK:
        print("WARNING: scikit-learn unavailable; kappa will be None.")

    results: list[dict[str, Any]] = []
    pooled = []
    for k in keys:
        print(f"\n[{k}] comparing...")
        r = compare_survey(k, args.v2_conf_threshold)
        results.append(r)
        x = r["summary"]

        # write deliverable + diagnostic CSVs
        r["_both_cand"][[c for c in _OUT_COLS if c in r["_both_cand"].columns]].to_csv(
            OUT_DIR / f"agreed_candidates_{k}.csv", index=False, encoding="utf-8")
        r["_demoted"][[c for c in _OUT_COLS if c in r["_demoted"].columns]].to_csv(
            OUT_DIR / f"v1cand_v2discard_{k}.csv", index=False, encoding="utf-8")
        r["_added"][[c for c in _OUT_COLS if c in r["_added"].columns]].to_csv(
            OUT_DIR / f"v2cand_v1discard_{k}.csv", index=False, encoding="utf-8")
        r["_gold"][[c for c in _OUT_COLS if c in r["_gold"].columns]].to_csv(
            OUT_DIR / f"gold_candidates_{k}.csv", index=False, encoding="utf-8")

        pooled.append(r["_binary_conf"])  # not used numerically; pooling below
        print(f"  candidates: v1={x['v1_candidates']} v2={x['v2_candidates']} "
              f"intersection={x['intersection_candidates']} "
              f"(retained {x['v1_retained_pct']}% of v1)")
        print(f"  binary candidate agreement {x['binary_candidate_agreement_pct']}% "
              f"(k={x['binary_candidate_kappa']})  "
              f"gold={x['gold_count']}")

    # pooled combined metrics: rebuild from per-survey merges
    combined: dict[str, Any] = {}
    if results:
        tot_int = sum(r["summary"]["intersection_candidates"] for r in results)
        tot_v1c = sum(r["summary"]["v1_candidates"] for r in results)
        tot_gold = sum(r["summary"]["gold_count"] for r in results)
        tot_n = sum(r["summary"]["n_common_pairs"] for r in results)
        tot_agree = sum(
            r["summary"]["binary_candidate_agreement_pct"] / 100
            * r["summary"]["n_common_pairs"] for r in results)
        combined = {
            "intersection_candidates": tot_int,
            "gold_count": tot_gold,
            "v1_retained_pct": round(tot_int / tot_v1c * 100, 2) if tot_v1c else 0.0,
            "binary_candidate_agreement_pct": round(tot_agree / tot_n * 100, 2)
            if tot_n else 0.0,
            "binary_candidate_kappa": None,  # pooled kappa needs raw rows; per-survey above
        }

    (OUT_DIR / "v1_v2_signal_stratified_summary.json").write_text(
        json.dumps(
            {**{r["survey"]: r["summary"] for r in results}, "combined": combined},
            indent=2),
        encoding="utf-8")
    report = write_report(results, combined, args.v2_conf_threshold, OUT_DIR)

    print(f"\nWrote report: {report}")
    print(f"Wrote deliverable CSVs to: {OUT_DIR}")
    print("\n" + "=" * 70)
    print("HEADLINE -- reproducibility of the harmonization candidate list")
    print("=" * 70)
    for r in results:
        x = r["summary"]
        print(f"  {r['survey'].upper():<8s} "
              f"binary k={x['binary_candidate_kappa']}  "
              f"intersection={x['intersection_candidates']}  "
              f"retained={x['v1_retained_pct']}%  gold={x['gold_count']}")
    if combined:
        print(f"  {'TOTAL':<8s} intersection={combined['intersection_candidates']}  "
              f"gold={combined['gold_count']}  "
              f"retained={combined['v1_retained_pct']}%")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
